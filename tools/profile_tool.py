# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-05-09
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
from qgis.core import (QgsMapLayer,
                       QgsPointLocator,
                       QgsSnappingUtils,
                       QgsGeometry,
                       QGis,
                       QgsTolerance,
                       QgsPoint,
                       QgsWKBTypes)
from qgis.gui import (QgsMapTool,
                      QgsMessageBar,
                      QgsRubberBand)
from PyQt4.QtCore import (Qt,
                          QCoreApplication)
from PyQt4.QtGui import (QMessageBox,
                         QColor)
from ..core.finder import Finder
from ..core.geometry_v2 import GeometryV2
from ..ui.profile_layers_dialog import ProfileLayersDialog
from ..ui.profile_dock_widget import ProfileDockWidget
from ..ui.profile_message_dialog import ProfileMessageDialog
from ..ui.profile_confirm_dialog import ProfileConfirmDialog


class ProfileTool(QgsMapTool):
    """
    Tool class for making a line elevation profile
    """

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.__canvas = iface.mapCanvas()
        self.__icon_path = ':/plugins/VDLTools/icons/profile_icon.png'
        self.__text = QCoreApplication.translate("VDLTools","Profile of a line")
        self.__lineLayer = None
        self.setCursor(Qt.ArrowCursor)
        self.__isChoosed = False
        self.__lastFeatureId = None
        self.__lastFeature = None
        self.__dockWdg = None
        self.__layDlg = None
        self.__msgDlg = None
        self.__confDlg = None
        self.__points = None
        self.__layers = None
        self.__features = None
        self.__inSelection = False
        self.__selectedIds = None
        self.__selectedStarts = None
        self.__selectedDirections = None
        self.__startVertex = None
        self.__endVertex = None
        self.__rubberSit = None
        self.__rubberDif = None

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

    def activate(self):
        """
        When the action is selected
        """
        QgsMapTool.activate(self)
        self.__dockWdg = ProfileDockWidget(self.__iface)
        self.__iface.addDockWidget(Qt.BottomDockWidgetArea, self.__dockWdg)
        self.__dockWdg.closeSignal.connect(self.__closed)
        self.__rubberSit = QgsRubberBand(self.__canvas, QGis.Point)
        self.__rubberDif = QgsRubberBand(self.__canvas, QGis.Point)
        color = QColor("red")
        color.setAlphaF(0.78)
        self.__rubberSit.setColor(color)
        self.__rubberSit.setIcon(4)
        self.__rubberSit.setIconSize(20)
        self.__rubberDif.setColor(color)
        self.__rubberDif.setIcon(2)
        self.__rubberDif.setIconSize(20)

    def __closed(self):
        self.__cancel()
        self.__iface.actionPan().trigger()

    def deactivate(self):
        """
        When the action is deselected
        """
        self.__canvas.scene().removeItem(self.__rubberSit)
        self.__rubberSit.reset()
        self.__rubberSit = None
        self.__canvas.scene().removeItem(self.__rubberDif)
        self.__rubberDif.reset()
        self.__rubberDif = None
        if self.__dockWdg:
            self.__dockWdg.close()
        QgsMapTool.deactivate(self)

    def __cancel(self):
        self.__lineLayer.removeSelection()
        self.__lastFeatureId = None
        self.__lastFeature = None
        self.__selectedIds = None
        self.__selectedDirections = None
        self.__startVertex = None
        self.__endVertex = None
        self.__inSelection = False
        self.__layDlg = None
        self.__msgDlg = None
        self.__confDlg = None

    def setEnable(self, layer):
        """
        To check if we can enable the action for the selected layer
        :param layer: selected layer
        """
        if layer and layer.type() == QgsMapLayer.VectorLayer and \
                        QGis.fromOldWkbType(layer.wkbType()) == QgsWKBTypes.LineStringZ:
            self.__lineLayer = layer
            self.action().setEnabled(True)
            return
        self.action().setEnabled(False)
        if self.__canvas.mapTool() == self:
            self.__iface.actionPan().trigger()
        if self.__dockWdg:
            self.__dockWdg.close()
        self.__lineLayer = None

    def __setLayerDialog(self):
        """
        To create a Profile Layers Dialog
        """
        pointLayers = self.__lineVertices()
        if len(pointLayers) > 0:
            self.__layDlg = ProfileLayersDialog(pointLayers)
            self.__layDlg.rejected.connect(self.__cancel)
            self.__layDlg.okButton().clicked.connect(self.__onLayOk)
            self.__layDlg.cancelButton().clicked.connect(self.__onLayCancel)
            self.__layDlg.show()
        else:
            self.__layers = []
            self.__layOk()

    def __setMessageDialog(self, situations, differences, names):
        """
        To create a Profile Message Dialog
        :param situations: elevation differences between line and points
        :param differences: elevation differences between lines
        :param names: layers names
        """
        self.__msgDlg = ProfileMessageDialog(situations, differences, names, self.__points)
        self.__msgDlg.rejected.connect(self.__cancel)
        self.__msgDlg.passButton().clicked.connect(self.__onMsgPass)
        self.__msgDlg.onLineButton().clicked.connect(self.__onMsgLine)
        self.__msgDlg.onPointsButton().clicked.connect(self.__onMsgPoints)

    def __setConfirmDialog(self, origin):
        """
        To create a Profile Confirm Dialog
        :param origin: '0' if we copy points elevations to line, '1' if we copy line elevation to points
        """
        self.__confDlg = ProfileConfirmDialog()
        if origin == 0 and self.__lineLayer.isEditable() is False:
            self.__confDlg.setMessage(
                QCoreApplication.translate("VDLTools","Do you really want to edit the LineString layer ?"))
            self.__confDlg.rejected.connect(self.__cancel)
            self.__confDlg.okButton().clicked.connect(self.__onConfirmLine)
            self.__confDlg.cancelButton().clicked.connect(self.__onConfirmCancel)
            self.__confDlg.show()
        elif origin != 0:
            situations = self.__msgDlg.getSituations()
            case = True
            for s in situations:
                layer = self.__layers[s['layer'] - 1]
                if layer.isEditable() is False:
                    case = False
                    break
            if case is False:
                self.__confDlg.setMessage(
                    QCoreApplication.translate("VDLTools","Do you really want to edit the Point layer(s) ?"))
                self.__confDlg.okButton().clicked.connect(self.__onConfirmPoints)
                self.__confDlg.cancelButton().clicked.connect(self.__onConfirmClose)
                self.__confDlg.show()
            else:
                self.__confirmPoints()
        else:
            self.__confirmLine()

    def __getPointLayers(self):
        """
        To get all points layers that can be used
        :return: layers list
        """
        layerList = []
        for layer in self.__iface.mapCanvas().layers():
            if layer.type() == QgsMapLayer.VectorLayer and QGis.fromOldWkbType(layer.wkbType()) == QgsWKBTypes.PointZ:
                    layerList.append(layer)
        return layerList

    def __onMsgPass(self):
        """
        When the Pass button in Profile Message Dialog is pushed
        """
        self.__msgDlg.reject()

    def __onConfirmCancel(self):
        """
        When the Cancel button in Profile Confirm Dialog is pushed
        """
        self.__confDlg.reject()

    def __onMsgLine(self):
        """
        When the Line button in Profile Message Dialog is pushed
        """
        self.__setConfirmDialog(0)

    def __onMsgPoints(self):
        """
        When the Points button in Profile Message Dialog is pushed
        """
        self.__setConfirmDialog(1)

    def __onConfirmLine(self):
        """
        When the Line button in Profile Confirm Dialog is pushed
        """
        self.__confDlg.accept()
        self.__confirmLine()

    def __confirmLine(self):
        """
        To change the elevations of certains vertices of the line
        """
        situations = self.__msgDlg.getSituations()
        num_lines = len(self.__selectedIds)
        points = []
        for s in situations:
            if s['point'] not in points:
                points.append(s['point'])
            else:
                QMessageBox(
                    QCoreApplication.translate("VDLTools","There is more than one elevation for the point ") +
                    str(s['point']))
                return
        self.__msgDlg.accept()
        lines = []
        for iden in self.__selectedIds:
            for f in self.__lineLayer.selectedFeatures():
                if f.id() == iden:
                    line, curved = GeometryV2.asLineV2(f.geometry())
                    lines.append(line)
                    break
        for s in situations:
            z = self.__points[s['point']]['z'][s['layer']+num_lines-1]
            for i in xrange(num_lines):
                if self.__points[s['point']]['z'][i]:
                    index = s['point']-self.__selectedStarts[i]
                    if self.__selectedDirections[i] is False:
                        index = lines[i].numPoints()-1-index
                    lines[i].setZAt(index, z)
        if not self.__lineLayer.isEditable():
            self.__lineLayer.startEditing()
        for i in xrange(len(lines)):
            geom = QgsGeometry(lines[i].clone())
            self.__lineLayer.changeGeometry(self.__selectedIds[i], geom)
            # self.__lineLayer.updateExtents()
        self.__dockWdg.clearData()
        self.__cancel()

    def __onConfirmPoints(self):
        """
        When the Points button in Profile Confirm Dialog is pushed
        """
        self.__confDlg.accept()
        self.__confirmPoints()

    def __confirmPoints(self):
        """
        To change the elevations of certain points
        """
        self.__msgDlg.accept()
        situations = self.__msgDlg.getSituations()
        num_lines = len(self.__selectedIds)
        for s in situations:
            layer = self.__layers[s['layer']-1]
            point = self.__features[s['point']][s['layer']-1]
            point_v2 = GeometryV2.asPointV2(point.geometry())
            newZ = point_v2.z()
            for i in xrange(num_lines):
                if self.__points[s['point']]['z'][i]:
                    newZ = self.__points[s['point']]['z'][i]
                    break
            point_v2.setZ(newZ)
            if not layer.isEditable():
                layer.startEditing()
            layer.changeGeometry(point.id(), QgsGeometry(point_v2))
            # layer.updateExtents()
        self.__dockWdg.clearData()
        self.__cancel()

    def __onLayCancel(self):
        """
        When the Cancel button in Profile Layers Dialog is pushed
        """
        self.__layDlg.reject()
        self.__isChoosed = False

    def __lineVertices(self):
        availableLayers = self.__getPointLayers()
        pointLayers = []
        self.__points = []
        self.__selectedStarts = []
        num = 0
        num_lines = len(self.__selectedIds)
        for iden in self.__selectedIds:
            self.__selectedStarts.append(max(0,len(self.__points)-1))
            direction = self.__selectedDirections[num]
            selected = None
            for f in self.__lineLayer.selectedFeatures():
                if f.id() == iden:
                    selected = f
                    break
            if selected is None:
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools","Error"),
                    QCoreApplication.translate("VDLTools","error on selected"), level=QgsMessageBar.CRITICAL)
                continue
            line_v2, curved = GeometryV2.asLineV2(selected.geometry())
            if direction:
                rg = xrange(line_v2.numPoints())
            else:
                rg = xrange(line_v2.numPoints()-1, -1, -1)
            for i in rg:
                pt_v2 = line_v2.pointN(i)
                x = pt_v2.x()
                y = pt_v2.y()
                doublon = False
                for item in self.__points:
                    if item['x'] == x and item['y'] == y:
                        item['z'][num] = pt_v2.z()
                        doublon = True
                        break
                if not doublon:
                    z = []
                    for j in xrange(num_lines):
                        if j == num:
                            z.append(pt_v2.z())
                        else:
                            z.append(None)
                    self.__points.append({'x': x, 'y': y, 'z': z})
                    for layer in availableLayers:
                        laySettings = QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Vertex, 0.03,
                                                                   QgsTolerance.LayerUnits)
                        f_l = Finder.findClosestFeatureAt(self.toMapCoordinates(layer, QgsPoint(x, y)), self.__canvas,
                                                    [laySettings])
                        if f_l:
                            if layer not in pointLayers:
                                pointLayers.append(layer)
            num += 1
        return pointLayers

    def __onLayOk(self):
        """
        When the Ok button in Profile Layers Dialog is pushed
        """
        self.__layDlg.accept()
        self.__layers = self.__layDlg.getLayers()
        self.__layOk()

    def __layOk(self):
        """
        To create the profile
        """
        self.__features = []

        for points in self.__points:
            feat = []
            x = points['x']
            y = points['y']
            z = points['z']
            for layer in self.__layers:
                laySettings = QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Vertex, 0.03, QgsTolerance.LayerUnits)
                f_l = Finder.findClosestFeatureAt(self.toMapCoordinates(layer, QgsPoint(x, y)), self.__canvas,
                                                    [laySettings])
                if f_l is None:
                    feat.append(None)
                    z.append(None)
                else:
                    feat.append(f_l[0])
                    point_v2 = GeometryV2.asPointV2(f_l[0].geometry())
                    zp = point_v2.z()
                    if zp is None or zp != zp:
                        z.append(0)
                    else:
                        z.append(zp)
            self.__features.append(feat)

        names = [self.__lineLayer.name()]
        for layer in self.__layers:
            names.append(layer.name())
        self.__calculateProfile(names)
        self.__isChoosed = False
        self.__cancel()

    def __contains(self, line, point):
        """
        To check if a position is a line vertex
        :param line: the line
        :param point: the position
        :return: the vertex id in the line, or -1
        """
        pos = 0
        if point is None:
            return -1
        for pt in line:
            if pt.x() == point.x() and pt.y() == point.y():
                return pos
            pos += 1
        return -1

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.__cancel()

    def canvasMoveEvent(self, event):
        """
        When the mouse is moved
        :param event: mouse event
        """
        if not self.__isChoosed:
            if self.__lineLayer:
                laySettings = QgsSnappingUtils.LayerConfig(self.__lineLayer, QgsPointLocator.All, 10,
                                                           QgsTolerance.Pixels)
                f_l = Finder.findClosestFeatureAt(event.mapPoint(), self.__canvas, [laySettings])
                if not self.__inSelection:
                    if f_l and self.__lastFeatureId != f_l[0].id():
                        self.__lastFeature = f_l[0]
                        self.__lastFeatureId = f_l[0].id()
                        self.__lineLayer.setSelectedFeatures([f_l[0].id()])
                    if f_l is None:
                        self.__cancel()
                else:
                    if f_l and (not self.__selectedIds or f_l[0].id() not in self.__selectedIds):
                        line = f_l[0].geometry().asPolyline()
                        if self.__contains(line, self.__endVertex) > -1:
                            self.__lastFeature = f_l[0]
                            self.__lastFeatureId = f_l[0].id()
                            features = self.__selectedIds + [f_l[0].id()]
                            self.__lineLayer.setSelectedFeatures(features)

                        elif self.__contains(line, self.__startVertex) > -1:
                            self.__lastFeature = f_l[0]
                            self.__lastFeatureId = f_l[0].id()
                            features = self.__selectedIds + [f_l[0].id()]
                            self.__lineLayer.setSelectedFeatures(features)

                        else:
                            self.__lineLayer.setSelectedFeatures(self.__selectedIds)
                            self.__lastFeatureId = None
                            self.__lastFeature = None

                if f_l is None:
                    if self.__selectedIds:
                        self.__lineLayer.setSelectedFeatures(self.__selectedIds)
                    self.__lastFeatureId = None
                    self.__lastFeature = None

    def canvasReleaseEvent(self, event):
        """
        When the mouse is clicked
        :param event: mouse event
        """
        self.__rubberSit.reset()
        self.__rubberDif.reset()
        if event.button() == Qt.RightButton:
            if self.__lineLayer.selectedFeatures() and self.__selectedIds:
                self.__isChoosed = True
                self.__setLayerDialog()
        elif event.button() == Qt.LeftButton:
            if self.__lastFeature and (not self.__selectedIds or self.__lastFeature.id() not in self.__selectedIds):
                self.__inSelection = True
                line = self.__lastFeature.geometry().asPolyline()
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools",
                                               "Select more lines with click left or process "
                                               "with click right (ESC to undo)"),
                    level=QgsMessageBar.INFO, duration=3)
                if self.__selectedIds is None:
                    self.__selectedIds = []
                    self.__startVertex = line[0]
                    self.__endVertex = line[-1]
                    self.__selectedDirections = []
                    self.__selectedDirections.append(True)  # direction du premier prime
                    self.__selectedIds.append(self.__lastFeatureId)
                else:
                    pos = self.__contains(line, self.__startVertex)
                    if pos > -1:
                        self.__selectedIds = [self.__lastFeatureId] + self.__selectedIds
                        if pos == 0:
                            direction = False
                            self.__startVertex = line[-1]
                        else:
                            direction = True
                            self.__startVertex = line[0]
                        self.__selectedDirections = [direction] + self.__selectedDirections
                    else:
                        pos = self.__contains(line, self.__endVertex)
                        self.__selectedIds.append(self.__lastFeatureId)
                        if pos == 0:
                            direction = True
                            self.__endVertex = line[-1]
                        else:
                            direction = False
                            self.__endVertex = line[0]
                        self.__selectedDirections.append(direction)
                    self.__lineLayer.setSelectedFeatures(self.__selectedIds)

    def __calculateProfile(self, names):
        """
        To calculate the profile and display it
        :param names: the names of the displayed layers
        """
        if self.__points is None:
            return
        self.__dockWdg.clearData()
        if len(self.__points) == 0:
            return
        self.__dockWdg.setProfiles(self.__points, len(self.__selectedIds))
        self.__dockWdg.attachCurves(names)

        situations = []
        differences = []
        for p in xrange(len(self.__points)):
            pt = self.__points[p]
            num_lines = len(self.__selectedIds)
            zz = []
            for i in xrange(num_lines):
                if pt['z'][i]:
                    zz.append(i)
            if len(zz) == 0:
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools","Warning"),
                    QCoreApplication.translate("VDLTools","no line z ?!?"), level=QgsMessageBar.WARNING)
            elif len(zz) == 1:
                z0 = pt['z'][zz[0]]
                tol = 0.01 * z0
                for i in xrange(num_lines, len(pt['z'])):
                    if pt['z'][i] is None:
                        continue
                    if abs(pt['z'][i]-z0) > tol:
                        situations.append({'point': p, 'layer': (i-num_lines+1), 'vertex': z0})
            elif len(zz) == 2:
                z0 = pt['z'][zz[0]]
                tol = 0.01 * z0
                if abs(pt['z'][zz[1]] - z0) > tol:
                    differences.append({'point': p, 'v1': z0, 'v2': pt['z'][zz[1]]})
                else:
                    for i in xrange(num_lines, len(pt['z'])):
                        if pt['z'][i] is None:
                            continue
                        if abs(pt['z'][i]-z0) > tol:
                            situations.append({'point': p, 'layer': (i-num_lines+1), 'vertex': z0})
            else:
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools","Warning"),
                    QCoreApplication.translate("VDLTools","more than 2 lines z ?!?"), level=QgsMessageBar.WARNING)

        if (len(situations) > 0) or (len(differences) > 0):
            self.__setMessageDialog(situations, differences, names)
            self.__rubberSit.reset()
            self.__rubberDif.reset()
            for situation in situations:
                pt = self.__points[situation['point']]
                point = QgsPoint(pt['x'], pt['y'])
                if self.__rubberSit.numberOfVertices() == 0:
                    self.__rubberSit.setToGeometry(QgsGeometry().fromPoint(point), None)
                else:
                    self.__rubberSit.addPoint(point)
            for difference in differences:
                pt = self.__points[difference['point']]
                point = QgsPoint(pt['x'], pt['y'])
                if self.__rubberDif.numberOfVertices() == 0:
                    self.__rubberDif.setToGeometry(QgsGeometry().fromPoint(point), None)
                else:
                    self.__rubberDif.addPoint(point)

            self.__msgDlg.show()
        else:
            self.__cancel()
