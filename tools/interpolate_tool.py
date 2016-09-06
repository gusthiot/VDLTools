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

from qgis.gui import (QgsMapTool,
                      QgsMessageBar,
                      QgsRubberBand)
from qgis.core import (QGis,
                       QgsProject,
                       QgsMapLayer,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointV2,
                       QgsVertexId)
from PyQt4.QtCore import (Qt,
                          QCoreApplication)
from PyQt4.QtGui import QColor
from ..core.finder import Finder
from ..core.geometry_v2 import GeometryV2
from ..ui.interpolate_confirm_dialog import InterpolateConfirmDialog

# TODO : selection ligne, puis selection segment/point/intersection
class InterpolateTool(QgsMapTool):

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.__canvas = iface.mapCanvas()
        self.__icon_path = ':/plugins/VDLTools/icons/interpolate_icon.png'
        self.__text = QCoreApplication.translate(
            "VDLTools","Interpolate the elevation of a vertex and a point in the middle of a line")
        # self.__oldTool = None
        self.__layer = None
        self.setCursor(Qt.ArrowCursor)
        self.__isEditing = False
        self.__lastFeatureId = None
        self.__layerList = None
        self.__lastLayer = None
        self.__confDlg = None
        self.__mapPoint = None
        self.__rubber = None
        self.__counter = 0
        self.__ownSettings = None
        self.__selectedFeature = None
        self.__linesSets = None

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
        # self.__oldTool = self.__canvas.mapTool()
        self.__canvas.setMapTool(self)

    def setOwnSettings(self, settings):
        """
        To set the settings
        :param settings: income settings
        """
        self.__ownSettings = settings

    def activate(self):
        """
        When the action is selected
        """
        QgsMapTool.activate(self)
        self.__updateList()
        self.__rubber = QgsRubberBand(self.__canvas, QGis.Point)
        color = QColor("red")
        color.setAlphaF(0.78)
        self.__rubber.setColor(color)
        self.__rubber.setIcon(4)
        self.__rubber.setIconSize(20)

    def deactivate(self):
        """
        When the action is deselected
        """
        self.__rubber.reset()
        QgsMapTool.deactivate(self)

    def startEditing(self):
        """
        To set the action as enable, as the layer is editable
        """
        self.action().setEnabled(True)
        self.__canvas.layersChanged.connect(self.__updateList)
        self.__canvas.scaleChanged.connect(self.__updateList)
        QgsProject.instance().snapSettingsChanged.connect(self.__updateList)
        self.__layer.editingStarted.disconnect(self.startEditing)
        self.__layer.editingStopped.connect(self.stopEditing)

    def stopEditing(self):
        """
        To set the action as disable, as the layer is not editable
        """
        self.action().setEnabled(False)
        self.__canvas.layersChanged.disconnect(self.__updateList)
        self.__canvas.scaleChanged.disconnect(self.__updateList)
        QgsProject.instance().snapSettingsChanged.disconnect(self.__updateList)
        self.__layer.editingStopped.disconnect(self.stopEditing)
        self.__layer.editingStarted.connect(self.startEditing)
        if self.__canvas.mapTool == self:
            self.__iface.actionPan().trigger()
        #     self.__canvas.setMapTool(self.__oldTool)

    def removeLayer(self):
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
        if layer is not None \
                and layer.type() == QgsMapLayer.VectorLayer \
                and layer.geometryType() == QGis.Point:

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
                self.__canvas.layersChanged.connect(self.__updateList)
                self.__canvas.scaleChanged.connect(self.__updateSnapperList)
                QgsProject.instance().snapSettingsChanged.connect(self.__updateSnapperList)
            else:
                self.action().setEnabled(False)
                self.__layer.editingStarted.connect(self.startEditing)
                self.__canvas.layersChanged.disconnect(self.__updateList)
                self.__canvas.scaleChanged.disconnect(self.__updateSnapperList)
                QgsProject.instance().snapSettingsChanged.disconnect(self.__updateSnapperList)
                if self.__canvas.mapTool == self:
                    self.__iface.actionPan().trigger()
                #    self.__canvas.setMapTool(self.__oldTool)
            return
        self.action().setEnabled(False)
        self.removeLayer()

    def __updateList(self):
        """
        To update the line layers list that we can use for interpolation
        """
        self.__layerList = []
        legend = self.__iface.legendInterface()
        scale = self.__iface.mapCanvas().scale()
        for layer in self.__iface.mapCanvas().layers():
            noUse, enabled, snappingType, unitType, tolerance, avoidIntersection = \
                QgsProject.instance().snapSettingsForLayer(layer.id())
            if layer.type() == QgsMapLayer.VectorLayer and layer.hasGeometryType() \
                    and layer.geometryType() == QGis.Line:
                if not layer.hasScaleBasedVisibility() or layer.minimumScale() < scale <= layer.maximumScale():
                    if legend.isLayerVisible(layer) and enabled:
                        layerSettings = {'layer': layer, 'tolerance': tolerance, 'unitType': unitType}
                        self.__layerList.append(layerSettings)

        if self.__ownSettings and self.__ownSettings.linesLayer():
            noUse, enabled, snappingType, unitType, tolerance, avoidIntersection = \
                QgsProject.instance().snapSettingsForLayer(self.__ownSettings.linesLayer().id())
            self.__linesSets = {'layer': self.__ownSettings.linesLayer(), 'tolerance': tolerance, 'unitType': unitType}

    def canvasMoveEvent(self, event):
        """
        When the mouse is moved
        :param event: mouse event
        """
        if not self.__isEditing and self.__layerList is not None:
            f_l = Finder.findClosestFeatureLayersAt(event.mapPoint(), self.__layerList, self)

            if f_l is not None and self.__lastFeatureId != f_l[0].id():
                f = f_l[0]
                self.__lastFeatureId = f.id()
                self.__lastLayer = f_l[1]
                self.__lastLayer.setSelectedFeatures([f.id()])
            if f_l is not None:
                if self.__counter > 2:
                    self.__rubber.reset()
                    snappedIntersection = self.__snapToIntersection(event.mapPoint(), f_l[0])
                    print f_l[1].name()
                    if snappedIntersection is None:
                        self.__rubber.setIcon(4)
                        line_v2, curved = GeometryV2.asLineV2(f_l[0].geometry())
                        vertex_v2 = QgsPointV2()
                        vertex_id = QgsVertexId()
                        line_v2.closestSegment(QgsPointV2(event.mapPoint()), vertex_v2, vertex_id, 0)
                        self.__rubber.setToGeometry(QgsGeometry(vertex_v2), None)
                    else:
                        self.__rubber.setIcon(1)
                        self.__rubber.setToGeometry(QgsGeometry(snappedIntersection), None)
                    self.__counter = 0
                else:
                    self.__counter += 1
            if f_l is None and self.__lastLayer is not None:
                self.__lastLayer.removeSelection()
                self.__rubber.reset()
                self.__lastFeatureId = None

    def canvasReleaseEvent(self, event):
        """
        When the mouse is clicked
        :param event: mouse event
        """
        if self.__lastLayer is not None:
            found_features = self.__lastLayer.selectedFeatures()
            if len(found_features) > 0:
                if len(found_features) < 1:
                    self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools","One feature at a time"),
                                                          level=QgsMessageBar.INFO)
                    return
                self.__selectedFeature = found_features[0]
                self.__isEditing = True
                self.__mapPoint = event.mapPoint()
                self.__confDlg = InterpolateConfirmDialog()
                if self.__lastLayer.isEditable() is True:
                    self.__confDlg.setMainLabel(QCoreApplication.translate("VDLTools","What do you want to do ?"))
                    self.__confDlg.setAllLabel(QCoreApplication.translate("VDLTools","Create point and new vertex"))
                    self.__confDlg.setVtLabel(QCoreApplication.translate("VDLTools","Create only the vertex"))
                self.__confDlg.okButton().clicked.connect(self.__onConfirmOk)
                self.__confDlg.cancelButton().clicked.connect(self.__onConfirmCancel)
                self.__confDlg.show()

    def __onConfirmCancel(self):
        """
        When the Cancel button in Interpolate Confirm Dialog is pushed
        """
        self.__confDlg.close()
        self.__lastLayer.removeSelection()
        self.__rubber.reset()
        self.__lastFeatureId = None
        self.__isEditing = False

    def __onConfirmOk(self):

        id = self.__confDlg.getCheckedId()
        self.__confDlg.close()

        withVertex = True
        withPoint = True
        if id == 1:
            withVertex = False
        else:
            if self.__lastLayer.isEditable() is False:
                self.__lastLayer.startEditing()
        if id == 2:
            withPoint = False

        line_v2, curved = GeometryV2.asLineV2(self.__selectedFeature.geometry())
        vertex_v2 = QgsPointV2()
        vertex_id = QgsVertexId()
        line_v2.closestSegment(QgsPointV2(self.__mapPoint), vertex_v2, vertex_id, 0)

        snappedIntersection = self.__snapToIntersection(self.__mapPoint, self.__selectedFeature)
        if snappedIntersection is not None:
            vertex_v2 = snappedIntersection

        x0 = line_v2.xAt(vertex_id.vertex-1)
        y0 = line_v2.yAt(vertex_id.vertex-1)
        d0 = Finder.sqrDistForCoords(x0, vertex_v2.x(), y0, vertex_v2.y())
        x1 = line_v2.xAt(vertex_id.vertex)
        y1 = line_v2.yAt(vertex_id.vertex)
        d1 = Finder.sqrDistForCoords(x1, vertex_v2.x(), y1, vertex_v2.y())
        z0 = line_v2.zAt(vertex_id.vertex-1)
        z1 = line_v2.zAt(vertex_id.vertex)
        vertex_v2.addZValue((d0*z1 + d1*z0)/(d0 + d1))

        if withPoint:
            pt_feat = QgsFeature(self.__layer.pendingFields())
            pt_feat.setGeometry(QgsGeometry(vertex_v2))
            self.__iface.openFeatureForm(self.__layer, pt_feat)
            # self.__layer.addFeature(pt_feat)

        if withVertex:
            line_v2.insertVertex(vertex_id, vertex_v2)
            self.__lastLayer.changeGeometry(self.__selectedFeature.id(), QgsGeometry(line_v2))
        self.__lastLayer.removeSelection()
        self.__rubber.reset()
        self.__lastFeatureId = None
        self.__selectedFeature = None
        self.__isEditing = False

    def __snapToIntersection(self, mapPoint, selectedFeature):
        """
        To check is we can snap a close intersection
        :param mapPoint: the point to check
        :param selectedFeature: the feature that can intersect another one
        :return: an intersection QgsPointV2 or none
        """
        f = Finder.findClosestFeatureAt(mapPoint, self.__linesSets, self)
        if f is None:
            return None
        intersect = Finder.intersect(selectedFeature.geometry(), f.geometry(), mapPoint)
        if intersect is not None:
            return QgsPointV2(intersect)
        else:
            return None

