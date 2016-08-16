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
                       QgsGeometry,
                       QGis,
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

    def __init__(self, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.__canvas = iface.mapCanvas()
        self.__icon_path = ':/plugins/VDLTools/icons/profile_icon.png'
        self.__text = QCoreApplication.translate("VDLTools","Profile of a line")
        # self.__oldTool = None
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
        return self.__icon_path

    def text(self):
        return self.__text

    def setTool(self):
        # self.__oldTool = self.__canvas.mapTool()
        self.__canvas.setMapTool(self)

    def activate(self):
        QgsMapTool.activate(self)
        self.__dockWdg = ProfileDockWidget(self.__iface)
        self.__iface.addDockWidget(Qt.BottomDockWidgetArea, self.__dockWdg)
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

    def deactivate(self):
        self.__rubberSit.reset()
        self.__rubberDif.reset()
        if self.__dockWdg is not None:
            self.__dockWdg.close()
        if QgsMapTool is not None:
            QgsMapTool.deactivate(self)

    def setEnable(self, layer):
        if layer is not None and layer.type() == QgsMapLayer.VectorLayer and \
                        QGis.fromOldWkbType(layer.wkbType()) == QgsWKBTypes.LineStringZ:
            self.__lineLayer = layer
            self.action().setEnabled(True)
            return
        self.action().setEnabled(False)
        if self.__canvas.mapTool == self:
            self.__iface.actionPan().trigger()
        #    self.__canvas.setMapTool(self.__oldTool)
        if self.__dockWdg is not None:
            self.__dockWdg.close()
        self.__lineLayer = None

    def __setLayerDialog(self, pointLayers):
        self.__layDlg = ProfileLayersDialog(pointLayers)
        self.__layDlg.okButton().clicked.connect(self.__onLayOk)
        self.__layDlg.cancelButton().clicked.connect(self.__onLayCancel)

    def __setMessageDialog(self, situations, differences, names):
        self.__msgDlg = ProfileMessageDialog(situations, differences, names, self.__points)
        self.__msgDlg.passButton().clicked.connect(self.__onMsgPass)
        self.__msgDlg.onLineButton().clicked.connect(self.__onMsgLine)
        self.__msgDlg.onPointsButton().clicked.connect(self.__onMsgPoints)

    def __setConfirmDialog(self, origin):
        self.__confDlg = ProfileConfirmDialog()
        if origin == 0 and self.__lineLayer.isEditable() is False:
            self.__confDlg.setMessage(
                QCoreApplication.translate("VDLTools","Do you really want to edit the LineString layer ?"))
            self.__confDlg.okButton().clicked.connect(self.__onConfirmLine)
            self.__confDlg.cancelButton().clicked.connect(self.__onConfirmClose)
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
        layerList = []
        for layer in self.__iface.mapCanvas().layers():
            if layer.type() == QgsMapLayer.VectorLayer and QGis.fromOldWkbType(layer.wkbType()) == QgsWKBTypes.PointZ:
                    layerList.append(layer)
        return layerList

    def __onMsgPass(self):
        self.__msgDlg.close()
        self.__selectedIds = None
        self.__selectedDirections = None
        self.__startVertex = None
        self.__endVertex = None
        self.__inSelection = False

    def __onConfirmClose(self):
        self.__confDlg.close()
        self.__selectedIds = None
        self.__selectedDirections = None
        self.__startVertex = None
        self.__endVertex = None
        self.__inSelection = False

    def __onMsgLine(self):
        self.__setConfirmDialog(0)

    def __onMsgPoints(self):
        self.__setConfirmDialog(1)

    def __onConfirmLine(self):
        self.__confDlg.close()
        self.__confirmLine()

    def __confirmLine(self):
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
        self.__msgDlg.close()
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
                if self.__points[s['point']]['z'][i] is not None:
                    index = s['point']-self.__selectedStarts[i]
                    if self.__selectedDirections[i] is False:
                        index = lines[i].numPoints()-1-index
                    lines[i].setZAt(index, z)
        if not self.__lineLayer.isEditable():
            self.__lineLayer.startEditing()
        for i in xrange(len(lines)):
            geom = QgsGeometry(lines[i].clone())
            self.__lineLayer.changeGeometry(self.__selectedIds[i], geom)
            self.__lineLayer.updateExtents()
            #  self.__lineLayer.commitChanges()
        self.__dockWdg.clearData()
        self.__lineLayer.removeSelection()
        self.__selectedIds = None
        self.__selectedDirections = None
        self.__startVertex = None
        self.__endVertex = None
        self.__inSelection = False

    def __onConfirmPoints(self):
        self.__confDlg.close()
        self.__confirmPoints()

    def __confirmPoints(self):
        self.__msgDlg.close()
        situations = self.__msgDlg.getSituations()
        num_lines = len(self.__selectedIds)
        for s in situations:
            layer = self.__layers[s['layer']-1]
            point = self.__features[s['point']][s['layer']-1]
            point_v2 = GeometryV2.asPointV2(point.geometry())
            newZ = point_v2.z()
            for i in xrange(num_lines):
                if self.__points[s['point']]['z'][i] is not None:
                    newZ = self.__points[s['point']]['z'][i]
                    break
            point_v2.setZ(newZ)
            if not layer.isEditable():
                layer.startEditing()
            layer.changeGeometry(point.id(), QgsGeometry(point_v2))
            layer.updateExtents()
            #  layer.commitChanges()
        self.__dockWdg.clearData()
        self.__selectedIds = None
        self.__selectedDirections = None
        self.__startVertex = None
        self.__endVertex = None
        self.__inSelection = False

    def __onLayCancel(self):
        self.__layDlg.close()
        self.__isChoosed = 0
        self.__lineLayer.removeSelection()
        self.__selectedIds = None
        self.__selectedDirections = None
        self.__startVertex = None
        self.__endVertex = None
        self.__inSelection = False

    def __onLayOk(self):
        self.__layDlg.close()
        self.__layers = self.__layDlg.getLayers()
        self.__features = []
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
                    feat = []
                    for layer in self.__layers:
                        vertex = self.toCanvasCoordinates(QgsPoint(x, y))
                        point = Finder.findClosestFeatureAt(vertex, layer, self, 3, True)
                        feat.append(point)
                        if point is None:
                            z.append(None)
                        else:
                            point_v2 = GeometryV2.asPointV2(point.geometry())
                            zp = point_v2.z()
                            if zp is None or zp != zp:
                                z.append(0)
                            else:
                                z.append(zp)
                    self.__points.append({'x': x, 'y': y, 'z': z})
                    self.__features.append(feat)
            num += 1

        # points = []
        # for key, p in pointz.items():
        #     if p is not None:
        #         pt = p[0].geometry().asPoint()
        #         i = 0
        #         for l in layers:
        #             if l == p[1]:
        #                 break
        #             i += 1
        #         attName = attributes[i]
        #         z = p[0].attribute(attName)
        #         points.append({'x': pt.x(), 'y': pt.y(), 'z': z})
        names = [self.__lineLayer.name()]
        for layer in self.__layers:
            names.append(layer.name())
        self.__calculateProfile(names)
        self.__isChoosed = 0

    @staticmethod
    def contains(line, point):
        pos = 0
        for pt in line:
            if pt.x() == point.x() and pt.y() == point.y():
                return pos
            pos += 1
        return -1

    def canvasMoveEvent(self, event):
        if not self.__isChoosed:
            if self.__lineLayer is not None:
                f = Finder.findClosestFeatureAt(event.pos(), self.__lineLayer, self)
                if not self.__inSelection:
                    if f is not None and self.__lastFeatureId != f.id():
                        self.__lastFeature = f
                        self.__lastFeatureId = f.id()
                        self.__lineLayer.setSelectedFeatures([f.id()])
                    if f is None:
                        self.__lineLayer.removeSelection()
                        self.__lastFeatureId = None
                        self.__selectedIds = None
                        self.__selectedDirections = None
                        self.__startVertex = None
                        self.__endVertex = None
                else:
                    if f is not None and self.__lastFeatureId != f.id():
                        line = f.geometry().asPolyline()
                        if self.contains(line, self.__endVertex) > -1:
                            self.__lastFeature = f
                            self.__lastFeatureId = f.id()
                            features = self.__selectedIds + [f.id()]
                            self.__lineLayer.setSelectedFeatures(features)

                        elif self.contains(line, self.__startVertex) > -1:
                            self.__lastFeature = f
                            self.__lastFeatureId = f.id()
                            features = self.__selectedIds + [f.id()]
                            self.__lineLayer.setSelectedFeatures(features)

                        else:
                            self.__lineLayer.setSelectedFeatures(self.__selectedIds)
                            self.__lastFeatureId = None
                            self.__lastFeature = None

                    if f is None and self.__selectedIds is not None:
                        self.__lineLayer.setSelectedFeatures(self.__selectedIds)
                        self.__lastFeatureId = None
                        self.__lastFeature = None

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            if self.__lineLayer.selectedFeatures() and self.__selectedIds:
                self.__isChoosed = 1
                pointLayers = self.__getPointLayers()
                self.__setLayerDialog(pointLayers)
                self.__layDlg.show()
        elif event.button() == Qt.LeftButton:
            if self.__lastFeature:
                self.__inSelection = True
                line = self.__lastFeature.geometry().asPolyline()
                if self.__selectedIds is None:
                    self.__selectedIds = []
                    self.__startVertex = line[0]
                    self.__endVertex = line[-1]
                    self.__selectedDirections = []
                    self.__selectedDirections.append(True)  # direction du premier prime
                    self.__selectedIds.append(self.__lastFeatureId)
                else:
                    pos = self.contains(line, self.__startVertex)
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
                        pos = self.contains(line, self.__endVertex)
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
        if self.__points is None:
            return
        self.__dockWdg.clearData()
        if len(self.__points) == 0:
            return
        self.__dockWdg.setProfiles(self.__points, len(self.__selectedIds))
        self.__dockWdg.drawVertLine()
        self.__dockWdg.attachCurves(names)

        situations = []
        differences = []
        for p in xrange(len(self.__points)):
            pt = self.__points[p]
            num_lines = len(self.__selectedIds)
            zz = []
            for i in xrange(num_lines):
                if pt['z'][i] is not None:
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
            self.__selectedIds = None
            self.__selectedDirections = None
            self.__startVertex = None
            self.__endVertex = None
            self.__inSelection = False

