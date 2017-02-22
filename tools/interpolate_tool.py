# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-05-30
        git sha              : $Format:%H$
        copyright            : (C) 2016 Ville de Lausanne
        author               : Christophe Gusthiot
        email                : christophe.gusthiot@lausanne.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import division
from past.utils import old_div

from qgis.gui import (QgsMapToolAdvancedDigitizing,
                      QgsMessageBar,
                      QgsRubberBand)
from qgis.core import (QGis,
                       QgsEditFormConfig,
                       QgsSnappingUtils,
                       QgsTolerance,
                       QgsPointLocator,
                       QgsVectorLayer,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointV2,
                       QgsVertexId)
from PyQt4.QtCore import (Qt,
                          QCoreApplication)
from PyQt4.QtGui import QColor, QMoveEvent
from ..core.finder import Finder
from ..core.geometry_v2 import GeometryV2
from ..ui.interpolate_confirm_dialog import InterpolateConfirmDialog


class InterpolateTool(QgsMapToolAdvancedDigitizing):
    """
    Map tool class to interpolate an elevation in the middle of a segment
    """

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        QgsMapToolAdvancedDigitizing.__init__(self, iface.mapCanvas(), iface.cadDockWidget())
        self.__iface = iface
        self.__icon_path = ':/plugins/VDLTools/icons/interpolate_icon.png'
        self.__text = QCoreApplication.translate(
            "VDLTools","Interpolate the elevation of a vertex and a point in the middle of a line")
        self.__layer = None
        self.setCursor(Qt.ArrowCursor)
        self.__isEditing = False
        self.__lastFeatureId = None
        self.__layerList = None
        self.__lastLayer = None
        self.__confDlg = None
        self.__mapPoint = None
        self.__rubber = None
        self.__selectedFeature = None
        self.__findVertex = False

    def icon_path(self):
        """
        To get the icon path
        :return: icon path
        """
        return self.__icon_path

    def text(self):
        """
        To get the menu text
        :return: menu text
        """
        return self.__text

    def setTool(self):
        """
        To set the current tool as this one
        """
        self.canvas().setMapTool(self)

    def activate(self):
        """
        When the action is selected
        """
        QgsMapToolAdvancedDigitizing.activate(self)
        self.__updateList()
        self.__rubber = QgsRubberBand(self.canvas(), QGis.Point)
        color = QColor("red")
        color.setAlphaF(0.78)
        self.__rubber.setColor(color)
        self.__rubber.setIcon(4)
        self.__rubber.setIconSize(20)
        self.canvas().layersChanged.connect(self.__updateList)
        self.canvas().scaleChanged.connect(self.__updateList)
        self.setMode(self.CaptureLine)

    def deactivate(self):
        """
        When the action is deselected
        """
        self.__done()
        self.__cancel()
        self.__rubber = None
        self.canvas().layersChanged.disconnect(self.__updateList)
        self.canvas().scaleChanged.disconnect(self.__updateList)
        QgsMapToolAdvancedDigitizing.deactivate(self)

    def startEditing(self):
        """
        To set the action as enable, as the layer is editable
        """
        self.action().setEnabled(True)
        self.__layer.editingStarted.disconnect(self.startEditing)
        self.__layer.editingStopped.connect(self.stopEditing)

    def stopEditing(self):
        """
        To set the action as disable, as the layer is not editable
        """
        self.action().setEnabled(False)
        self.__layer.editingStopped.disconnect(self.stopEditing)
        self.__layer.editingStarted.connect(self.startEditing)
        if self.canvas().mapTool() == self:
            self.__iface.actionPan().trigger()

    def __done(self):
        """
        When the edition is finished
        """
        self.__isEditing = False
        self.__confDlg = None
        self.__mapPoint = None

    def __cancel(self):
        """
        To cancel used variables
        """
        self.__findVertex = False
        if self.__lastLayer is not None:
            self.__lastLayer.removeSelection()
            self.__lastLayer = None
        self.__rubber.reset()
        self.__lastFeatureId = None
        self.__selectedFeature = None

    def __removeLayer(self):
        """
        To remove the current working layer
        """
        if self.__layer is not None:
            if self.__layer.isEditable():
                self.__layer.editingStopped.disconnect(self.stopEditing)
            else:
                self.__layer.editingStarted.disconnect(self.startEditing)
            self.__layer = None

    def setEnable(self, layer):
        """
        To check if we can enable the action for the selected layer
        :param layer: selected layer
        """
        if layer is not None and isinstance(layer, QgsVectorLayer) and layer.geometryType() == QGis.Point:
            if layer == self.__layer:
                return

            if self.__layer is not None:
                if self.__layer.isEditable():
                    self.__layer.editingStopped.disconnect(self.stopEditing)
                else:
                    self.__layer.editingStarted.disconnect(self.startEditing)
            self.__layer = layer
            if self.__layer.isEditable():
                self.action().setEnabled(True)
                self.__layer.editingStopped.connect(self.stopEditing)
            else:
                self.action().setEnabled(False)
                self.__layer.editingStarted.connect(self.startEditing)
                if self.canvas().mapTool() == self:
                    self.__iface.actionPan().trigger()
            return
        if self.canvas().mapTool() == self:
            self.__iface.actionPan().trigger()
        self.action().setEnabled(False)
        self.__removeLayer()

    def __updateList(self):
        """
        To update the line layers list that we can use for interpolation
        """
        self.__layerList = []
        for layer in self.canvas().layers():
            if isinstance(layer, QgsVectorLayer) and layer.hasGeometryType() \
                    and layer.geometryType() == QGis.Line:
                        self.__layerList.append(QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.All, 10,
                                                                             QgsTolerance.Pixels))

    def keyReleaseEvent(self, event):
        """
        When keyboard is pressed
        :param event: keyboard event
        """
        if event.key() == Qt.Key_Escape:
            self.__done()
            self.__cancel()

    def cadCanvasMoveEvent(self, event):
        """
        When the mouse is moved
        :param event: mouse event
        """

        if type(event) == QMoveEvent:
            map_point = self.toMapCoordinates(event.pos())
        else:
            map_point = event.mapPoint()

        if not self.__isEditing and not self.__findVertex and self.__layerList is not None:
            f_l = Finder.findClosestFeatureAt(map_point, self.canvas(), self.__layerList)

            if f_l is not None and self.__lastFeatureId != f_l[0].id():
                f = f_l[0]
                self.__lastFeatureId = f.id()
                if self.__lastLayer is not None:
                    self.__lastLayer.removeSelection()
                self.__lastLayer = f_l[1]
                self.__lastLayer.setSelectedFeatures([f.id()])
            if f_l is None and self.__lastLayer is not None:
                self.__lastLayer.removeSelection()
                self.__lastFeatureId = None
        elif self.__findVertex:
            self.__rubber.reset()
            snap_layers = Finder.getLayersSettings(self.canvas(), [QGis.Line, QGis.Polygon], QgsPointLocator.All)
            match = Finder.snap(map_point, self.canvas(), snap_layers, QgsSnappingUtils.SnapAdvanced)
            if match.hasVertex() or match.hasEdge():
                point = match.point()
                if match.hasVertex():
                    if match.layer() is not None and self.__selectedFeature.id() == match.featureId():
                        self.__rubber.setIcon(4)
                        self.__rubber.setToGeometry(QgsGeometry().fromPoint(point), None)
                    else:
                        intersection = Finder.snapCurvedIntersections(match.point(), self.canvas(), self,
                                                                      self.__selectedFeature.id())
                        if intersection is not None:
                            self.__rubber.setIcon(1)
                            self.__rubber.setToGeometry(QgsGeometry().fromPoint(intersection), None)
                if match.hasEdge():
                    intersection = Finder.snapCurvedIntersections(match.point(), self.canvas(), self,
                                                                  self.__selectedFeature.id())
                    if intersection is not None:
                        self.__rubber.setIcon(1)
                        self.__rubber.setToGeometry(QgsGeometry().fromPoint(intersection), None)
                    elif self.__selectedFeature.id() == match.featureId():
                        self.__rubber.setIcon(3)
                        self.__rubber.setToGeometry(QgsGeometry().fromPoint(point), None)

    def cadCanvasReleaseEvent(self, event):
        """
        When the mouse is clicked
        :param event: mouse event
        """
        if self.__lastLayer is not None and not self.__findVertex:
            found_features = self.__lastLayer.selectedFeatures()
            if len(found_features) > 0:
                if len(found_features) > 1:
                    self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools","One feature at a time"),
                                                          level=QgsMessageBar.INFO)
                    return
                self.__selectedFeature = found_features[0]

                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools",
                                               "Select the position for interpolation (ESC to undo)"),
                    level=QgsMessageBar.INFO, duration=3)
                self.setMode(self.CaptureNone)
                self.__findVertex = True
        elif self.__findVertex:
            self.__rubber.reset()
            snap_layers = Finder.getLayersSettings(self.canvas(), [QGis.Line, QGis.Polygon], QgsPointLocator.All)
            match = Finder.snap(event.mapPoint(), self.canvas(), snap_layers, QgsSnappingUtils.SnapAdvanced)
            if match.hasVertex() or match.hasEdge():
                point = match.point()
                ok = False
                if match.hasVertex():
                    if match.layer() is not None and self.__selectedFeature.id() == match.featureId():
                        ok = True
                    else:
                        intersection = Finder.snapCurvedIntersections(match.point(), self.canvas(), self,
                                                                      self.__selectedFeature.id())
                        if intersection is not None:
                            point = intersection
                            ok = True
                if match.hasEdge():
                    intersection = Finder.snapCurvedIntersections(match.point(), self.canvas(), self,
                                                                  self.__selectedFeature.id())
                    if intersection is not None:
                        point = intersection
                        ok = True
                    elif self.__selectedFeature.id() == match.featureId():
                        ok = True
                if ok:
                    self.__isEditing = True
                    self.__findVertex = False
                    self.__mapPoint = point
                    if not match.hasVertex() or match.featureId() == 0:
                        self.__confDlg = InterpolateConfirmDialog()
                        if self.__lastLayer.isEditable():
                            self.__confDlg.setMainLabel(QCoreApplication.translate("VDLTools","What do you want to do ?"))
                            self.__confDlg.setAllLabel(QCoreApplication.translate("VDLTools","Create point and new vertex"))
                            self.__confDlg.setVtLabel(QCoreApplication.translate("VDLTools","Create only the vertex"))
                        self.__confDlg.rejected.connect(self.__done)
                        self.__confDlg.okButton().clicked.connect(self.__onConfirmOk)
                        self.__confDlg.cancelButton().clicked.connect(self.__onConfirmCancel)
                        self.__confDlg.show()
                    else:
                        self.__ok(False, True)
            else:
                self.__done()
                self.__cancel()

    def __onConfirmCancel(self):
        """
        When the Cancel button in Interpolate Confirm Dialog is pushed
        """
        self.__confDlg.reject()

    def __onConfirmOk(self):
        """
        When the Ok button in Interpolate Confirm Dialog is pushed
        """
        checkedId = self.__confDlg.getCheckedId()
        self.__confDlg.accept()

        withVertex = True
        withPoint = True
        if checkedId == 1:
            withVertex = False
        else:
            if not self.__lastLayer.isEditable():
                self.__lastLayer.startEditing()
        if checkedId == 2:
            withPoint = False

        self.__ok(withVertex, withPoint)

    def __ok(self, withVertex, withPoint):
        """
        To realize the interpolation
        :param withVertex: if we want a new interpolated vertex
        :param withPoint: if we want a new interpolated point
        """
        line_v2, curved = GeometryV2.asLineV2(self.__selectedFeature.geometry(), self.__iface)
        vertex_v2 = QgsPointV2()
        vertex_id = QgsVertexId()
        line_v2.closestSegment(QgsPointV2(self.__mapPoint), vertex_v2, vertex_id, 0)

        x0 = line_v2.xAt(vertex_id.vertex-1)
        y0 = line_v2.yAt(vertex_id.vertex-1)
        d0 = Finder.sqrDistForCoords(x0, vertex_v2.x(), y0, vertex_v2.y())
        x1 = line_v2.xAt(vertex_id.vertex)
        y1 = line_v2.yAt(vertex_id.vertex)
        d1 = Finder.sqrDistForCoords(x1, vertex_v2.x(), y1, vertex_v2.y())
        z0 = line_v2.zAt(vertex_id.vertex-1)
        z1 = line_v2.zAt(vertex_id.vertex)
        vertex_v2.addZValue(old_div((d0*z1 + d1*z0),(d0 + d1)))

        if withPoint:
            pt_feat = QgsFeature(self.__layer.pendingFields())
            pt_feat.setGeometry(QgsGeometry(vertex_v2))

            if self.__layer.editFormConfig().suppress() == QgsEditFormConfig.SuppressOn:
                self.__layer.addFeature(pt_feat)
            else:
                self.__iface.openFeatureForm(self.__layer, pt_feat)

        if withVertex:
            line_v2.insertVertex(vertex_id, vertex_v2)
            self.__lastLayer.changeGeometry(self.__selectedFeature.id(), QgsGeometry(line_v2))

        self.__done()
        self.__findVertex = True
