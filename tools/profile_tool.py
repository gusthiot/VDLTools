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
from builtins import str
from builtins import range
from qgis.core import (QgsMapLayer,
                       Qgis,
                       QgsVertexId,
                       QgsSnappingConfig,
                       QgsGeometry,
                       QgsTolerance,
                       QgsPoint,
                       QgsPointXY,
                       QgsWkbTypes)
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtGui import QColor
from ..core.finder import Finder
from ..core.geometry_v2 import GeometryV2
from ..ui.profile_layers_dialog import ProfileLayersDialog
from ..ui.profile_dock_widget import ProfileDockWidget
from ..ui.profile_message_dialog import ProfileMessageDialog
from ..ui.profile_confirm_dialog import ProfileConfirmDialog
from ..ui.profile_zeros_dialog import ProfileZerosDialog
from ..ui.profile_force_dialog import ProfileForceDialog


class ProfileTool(QgsMapTool):
    """
    Tool class for making a line elevation profile
    """

    ALT_TOLERANCE = 0.0005
    SEARCH_TOLERANCE = 0.001

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.icon_path = ':/plugins/VDLTools/icons/profile_icon.png'
        self.text = QCoreApplication.translate("VDLTools", "Profile of a line")
        self.__lineLayer = None
        self.setCursor(Qt.ArrowCursor)
        self.__isChoosed = False
        self.__lastFeatureId = None
        self.__lastFeature = None
        self.__dockWdg = None
        self.__layDlg = None
        self.__msgDlg = None
        self.__confDlg = None
        self.__zeroDlg = None
        self.__forceDlg = None
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
        self.ownSettings = None
        self.__usedMnts = None
        self.__isfloating = False
        self.__dockGeom = None

    def setTool(self):
        """
        To set the current tool as this one
        """
        self.canvas().setMapTool(self)

    def activate(self):
        """
        When the action is selected
        """
        QgsMapTool.activate(self)
        self.__dockWdg = ProfileDockWidget(self.__iface, self.__dockGeom)
        if self.__isfloating:
            self.__dockWdg.show()
        else:
           self.__iface.addDockWidget(Qt.BottomDockWidgetArea, self.__dockWdg)
        self.__dockWdg.closeSignal.connect(self.__closed)
        self.__rubberSit = QgsRubberBand(self.canvas(), QgsWkbTypes.PointGeometry)
        self.__rubberDif = QgsRubberBand(self.canvas(), QgsWkbTypes.PointGeometry)
        color = QColor("red")
        color.setAlphaF(0.78)
        self.__rubberSit.setColor(color)
        self.__rubberSit.setIcon(4)
        self.__rubberSit.setIconSize(20)
        self.__rubberDif.setColor(color)
        self.__rubberDif.setIcon(2)
        self.__rubberDif.setIconSize(20)

    def __closed(self):
        """
        When the dock is closed
        """
        self.__dockGeom = self.__dockWdg.geometry()
        self.__isfloating = self.__dockWdg.isFloating()
        self.__cancel()
        self.__iface.actionPan().trigger()

    def deactivate(self):
        """
        When the action is deselected
        """
        self.canvas().scene().removeItem(self.__rubberDif)
        self.__rubberDif = None
        self.canvas().scene().removeItem(self.__rubberSit)
        self.__rubberSit = None
        if self.__dockWdg is not None:
            self.__dockWdg.close()
        QgsMapTool.deactivate(self)

    def __cancel(self):
        """
        To cancel used variables
        """
        if self.__lineLayer is not None:
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
        self.__zeroDlg = None
        self.__forceDlg = None
        self.__isChoosed = False

    def setEnable(self, layer):
        """
        To check if we can enable the action for the selected layer
        :param layer: selected layer
        """
        if layer is not None and layer.type() == QgsMapLayer.VectorLayer and \
                GeometryV2.getAdaptedWKB(layer.wkbType()) == QgsWkbTypes.LineStringZ:
            self.__lineLayer = layer
            self.action().setEnabled(True)
            return
        self.action().setEnabled(False)
        if self.canvas().mapTool() == self:
            self.__iface.actionPan().trigger()
        if self.__dockWdg is not None:
            self.__dockWdg.close()
        self.__lineLayer = None

    def __setLayerDialog(self):
        """
        To create a Profile Layers Dialog
        """
        otherLayers = self.__lineVertices(True)
        with_mnt = True
        if self.ownSettings is None or self.ownSettings.mntUrl is None \
                or self.ownSettings.mntUrl == "":
            with_mnt = False
        if not with_mnt and len(otherLayers) == 0:
            self.__layers = []
            self.__layOk()
        else:
            self.__layDlg = ProfileLayersDialog(otherLayers, with_mnt)
            self.__layDlg.rejected.connect(self.__cancel)
            self.__layDlg.okButton().clicked.connect(self.__onLayOk)
            self.__layDlg.cancelButton().clicked.connect(self.__onLayCancel)
            self.__layDlg.show()

    def __setMessageDialog(self, situations, differences, names):
        """
        To create a Profile Message Dialog
        :param situations: elevation differences between line and points
        :param differences: elevation differences between lines
        :param names: layers names
        """
        self.__msgDlg = ProfileMessageDialog(situations, differences, names, self.__points)
        self.__msgDlg.rejected.connect(self.__checkZeros)
        self.__msgDlg.passButton().clicked.connect(self.__onMsgPass)
        self.__msgDlg.onLineButton().clicked.connect(self.__onMsgLine)
        self.__msgDlg.onPointsButton().clicked.connect(self.__onMsgPoints)

    def __setConfirmDialog(self, origin):
        """
        To create a Profile Confirm Dialog
        :param origin: '0' if we copy points elevations to line, '1' if we copy line elevation to points
        """
        self.__confDlg = ProfileConfirmDialog()
        if origin == 0 and not self.__lineLayer.isEditable():
            self.__confDlg.setMessage(
                QCoreApplication.translate("VDLTools", "Do you really want to edit the LineString layer ?"))
            self.__confDlg.rejected.connect(self.__checkZeros)
            self.__confDlg.okButton().clicked.connect(self.__onConfirmLine)
            self.__confDlg.cancelButton().clicked.connect(self.__onConfirmCancel)
            self.__confDlg.show()
        elif origin != 0:
            situations = self.__msgDlg.getSituations()
            case = True
            for s in situations:
                layer = self.__layers[s['layer'] - 1]
                if not layer.isEditable():
                    case = False
                    break
            if not case:
                self.__confDlg.setMessage(
                    QCoreApplication.translate("VDLTools", "Do you really want to edit the Point layer(s) ?"))
                self.__confDlg.rejected.connect(self.__checkZeros)
                self.__confDlg.okButton().clicked.connect(self.__onConfirmPoints)
                self.__confDlg.cancelButton().clicked.connect(self.__onConfirmCancel)
                self.__confDlg.show()
            else:
                self.__confirmPoints()
        else:
            self.__confirmLine()

    def __getOtherLayers(self):
        """
        To get all points layers that can be used
        :return: layers list
        """
        layerList = []
        types = [QgsWkbTypes.PointZ, QgsWkbTypes.LineStringZ, QgsWkbTypes.CircularStringZ, QgsWkbTypes.CompoundCurveZ,
                 QgsWkbTypes.CurvePolygonZ, QgsWkbTypes.PolygonZ]
        for layer in self.canvas().layers():
            if layer.type() == QgsMapLayer.VectorLayer and GeometryV2.getAdaptedWKB(layer.wkbType()) in types:
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

    def __checkZeros(self):
        """
        To check if there are zeros in selected objects
        """
        alts = []
        nb_not_none = []
        for i in range(len(self.__points)):
            zz = self.__points[i]['z']
            alt = 0
            nb = 0
            for z in zz:
                if z is not None:
                    if isinstance(z, list):
                        for za in z:
                            if za is not None:
                                nb += 1
                                if za > alt:
                                    alt = za
                    else:
                        nb += 1
                        if z > alt:
                            alt = z
            alts.append(alt)
            nb_not_none.append(nb)

        self.__zeros = []
        self.__extras = []
        for i in range(len(self.__points)):
            if alts[i] == 0:
                last = len(self.__points)-1
                if i == 0:
                    ap = alts[1]
                    if len(self.__points) > 2:
                        app = alts[2]
                    else:
                        app = 0
                    if ap == 0 or app == 0:
                        self.__zeros.append([0, None, None, None])
                    else:
                        big_d = Finder.sqrDistForCoords(self.__points[1]['x'], self.__points[2]['x'],
                                                        self.__points[1]['y'], self.__points[2]['y'])
                        small_d = Finder.sqrDistForCoords(self.__points[0]['x'], self.__points[1]['x'],
                                                          self.__points[0]['y'], self.__points[1]['y'])
                        zextra = round(app + (1 + small_d / big_d) * (ap - app), 3)
                        if small_d < (big_d / 4):
                            self.__zeros.append([0, zextra, nb_not_none[0], 'E'])
                        else:
                            self.__zeros.append([0, None, None, 'E'])
                            self.__extras.append([0, zextra, len(self.__zeros)-1, nb_not_none[0]])
                elif i == last:
                    av = alts[last-1]
                    if len(self.__points) > 2:
                        avv = alts[last-2]
                    else:
                        avv = 0
                    if av == 0 or avv == 0:
                        self.__zeros.append([last, None, None, None])
                    else:
                        big_d = Finder.sqrDistForCoords(self.__points[last-1]['x'], self.__points[last-2]['x'],
                                                        self.__points[last-1]['y'], self.__points[last-2]['y'])
                        small_d = Finder.sqrDistForCoords(self.__points[last]['x'], self.__points[last-1]['x'],
                                                          self.__points[last]['y'], self.__points[last-1]['y'])
                        zextra = round(avv + (1 + small_d / big_d) * (av - avv), 3)
                        if small_d < (big_d / 4):
                            self.__zeros.append([last, zextra, nb_not_none[last], 'E'])
                        else:
                            self.__zeros.append([last, None, None, 'E'])
                            self.__extras.append([last, zextra, len(self.__zeros)-1, nb_not_none[last]])
                else:
                    av = None
                    j = 1
                    while True:
                        if i-j < 0:
                            break
                        if alts[i-j] != 0:
                            av = j
                            break
                        j += 1
                    ap = None
                    j = 1
                    while True:
                        if i+j > last:
                            break
                        if alts[i+j] != 0:
                            ap = j
                            break
                        j += 1
                    if av is None or ap is None:
                        self.__zeros.append([i, None, None, None])
                    else:
                        d0 = Finder.sqrDistForCoords(
                            self.__points[i-av]['x'], self.__points[i]['x'], self.__points[i-av]['y'],
                            self.__points[i]['y'])
                        d1 = Finder.sqrDistForCoords(
                            self.__points[i+ap]['x'], self.__points[i]['x'], self.__points[i+ap]['y'],
                            self.__points[i]['y'])
                        zinter = round((d0*alts[i+ap] + d1*alts[i-av]) / (d0 + d1), 3)
                        self.__zeros.append([i, zinter, nb_not_none[i], 'I'])

        if len(self.__extras) == 0:
            self.__setZerosDialog()
        else:
            self.__checkForceExtrapolation()

    def __checkForceExtrapolation(self):
        """
        To ask for forcing extrapolation
        """
        message = ""
        for extra in self.__extras:
            message += str(extra[0]) + ") " + \
                       QCoreApplication.translate("VDLTools",
                                                  "The segment is too big, do you really want "
                                                  "to extrapolate anyway ? (elevation : ") + \
                       str(extra[1]) + "m) ? \n"
        self.__forceDlg = ProfileForceDialog(message)
        self.__forceDlg.okButton().clicked.connect(self.__onForceOk)
        self.__forceDlg.cancelButton().clicked.connect(self.__onForceCancel)
        self.__forceDlg.show()

    def __onForceOk(self):
        """
        When the Ok button in Profile Force Dialog is pushed
        """
        self.__forceDlg.accept()
        for extra in self.__extras:
            self.__zeros[extra[2]] = [extra[0], extra[1], extra[3], 'E']
        self.__setZerosDialog()

    def __onForceCancel(self):
        """
        When the Cancel button in Profile Force Dialog is pushed
        """
        self.__forceDlg.reject()
        self.__setZerosDialog()

    def __setZerosDialog(self):

        if len(self.__zeros) > 0:
            self.__zeroDlg = ProfileZerosDialog(self.__zeros)
            self.__zeroDlg.rejected.connect(self.__cancel)
            self.__zeroDlg.passButton().clicked.connect(self.__onZeroPass)
            self.__zeroDlg.applyButton().clicked.connect(self.__onZeroApply)
            self.__zeroDlg.show()
        else:
            self.__cancel()

    def __onZeroPass(self):
        """
        When the Pass button in Profile Zeros Dialog is pushed
        """
        self.__zeroDlg.reject()

    def __onZeroApply(self):
        """
        When the Apply button in Profile Zeros Dialog is pushed
        """
        self.__zeroDlg.accept()
        zeros = self.__zeroDlg.getZeros()

        num_lines = len(self.__selectedIds)
        lines = []
        for iden in self.__selectedIds:
            for f in self.__lineLayer.selectedFeatures():
                if f.id() == iden:
                    line = f.geometry().constGet().clone()
                    lines.append(line)
                    break
        for z in zeros:
            for i in range(num_lines):
                if self.__points[z[0]]['z'][i] is not None:
                    index = z[0]-self.__selectedStarts[i]
                    if not self.__selectedDirections[i]:
                        index = lines[i].numPoints()-1-index
                    lines[i].setZAt(index, z[1])
            if z[2] > 1:
                zz = self.__points[z[0]]['z']
                for p in range(len(zz)-num_lines):
                    if zz[num_lines+p] is not None:
                        feat = self.__features[z[0]][p]
                        layer = self.__layers[p]
                        self.__changePoint(layer, z[0], feat, z[1])
        if not self.__lineLayer.isEditable():
            self.__lineLayer.startEditing()
        for i in range(len(lines)):
            geom = QgsGeometry(lines[i].clone())
            self.__lineLayer.changeGeometry(self.__selectedIds[i], geom)
        self.__dockWdg.clearData()
        self.__lineVertices()
        self.__createProfile()
        self.__cancel()

    def __confirmLine(self):
        """
        To change the elevations of some vertices of the line
        """
        situations = self.__msgDlg.getSituations()
        num_lines = len(self.__selectedIds)
        points = {}
        for s in situations:
            point = self.__points[s['point']]['z'][s['layer']+num_lines-1]
            if 'poz' in s:
                point = point[s['poz']]
            if s['point'] not in points:
                points[s['point']] = point
            else:
                diff = abs(point - points[s['point']])
                if diff > 0.001:
                    QMessageBox.information(
                        None, QCoreApplication.translate("VDLTools", "Elevation"),
                        QCoreApplication.translate("VDLTools", "There is more than one elevation for the point ") +
                        str(s['point'])
                    )
                    return
        self.__msgDlg.accept()
        lines = []
        for iden in self.__selectedIds:
            for f in self.__lineLayer.selectedFeatures():
                if f.id() == iden:
                    line = self.f.geometry().constGet().clone()
                    lines.append(line)
                    break
        for s in situations:
            z = self.__points[s['point']]['z'][s['layer']+num_lines-1]
            if 'poz' in s:
                z = z[s['poz']]
            for i in range(num_lines):
                if self.__points[s['point']]['z'][i] is not None:
                    index = s['point']-self.__selectedStarts[i]
                    if not self.__selectedDirections[i]:
                        index = lines[i].numPoints()-1-index
                    lines[i].setZAt(index, z)
        if not self.__lineLayer.isEditable():
            self.__lineLayer.startEditing()
        for i in range(len(lines)):
            geom = QgsGeometry(lines[i].clone())
            self.__lineLayer.changeGeometry(self.__selectedIds[i], geom)
        self.__dockWdg.clearData()
        self.__lineVertices()
        self.__createProfile()
        self.__checkZeros()

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
            feat = self.__features[s['point']][s['layer']-1]
            if 'poz' in s:
                feat = feat[s['poz']]
            newZ = 0
            for i in range(num_lines):
                if self.__points[s['point']]['z'][i] is not None:
                    newZ = self.__points[s['point']]['z'][i]
                    break
            self.__changePoint(layer, s['point'], feat, newZ)
        self.__dockWdg.clearData()
        self.__lineVertices()
        self.__createProfile()
        self.__checkZeros()

    def __changePoint(self, layer, pos, feat, newZ):
        """
        To change Vertex elevation
        :param layer: layer containing the object
        :param pos: vertex position in the object (if not a point)
        :param feat: QgsFeature of the object
        :param newZ: new elevation
        """
        if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            closest = feat.geometry().closestVertex(QgsPointXY(self.__points[pos]['x'], self.__points[pos]['y']))
            feat_v2 = feat.geometry().constGet().clone()
            position = ProfileTool.polygonVertexId(feat_v2, closest[1])
            vertex = feat_v2.vertexAt(position)
            feat_v2.deleteVertex(position)
            vertex.setZ(newZ)
            feat_v2.insertVertex(position, vertex)
        elif layer.geometryType() == QgsWkbTypes.LineGeometry:
            closest = feat.geometry().closestVertex(QgsPointXY(self.__points[pos]['x'], self.__points[pos]['y']))
            feat_v2 = feat.geometry().constGet().clone()
            feat_v2.setZAt(closest[1], newZ)
        else:
            feat_v2 = feat.geometry().constGet().clone()
            feat_v2.setZ(newZ)
        if not layer.isEditable():
            layer.startEditing()
        layer.changeGeometry(feat.id(), QgsGeometry(feat_v2))

    def __onLayCancel(self):
        """
        When the Cancel button in Profile Layers Dialog is pushed
        """
        self.__layDlg.reject()
        self.__isChoosed = False

    def __lineVertices(self, checkLayers=False):
        """
        To check if vertices of others layers are crossing the displaying line
        :param checkLayers: if we want to get the list of the other layers in return
        :return: other layers list if requested
        """
        if checkLayers:
            availableLayers = self.__getOtherLayers()
            otherLayers = []
        self.__points = []
        self.__selectedStarts = []
        num = 0
        num_lines = len(self.__selectedIds)
        for iden in self.__selectedIds:
            self.__selectedStarts.append(max(0, len(self.__points)-1))
            direction = self.__selectedDirections[num]
            selected = None
            for f in self.__lineLayer.selectedFeatures():
                if f.id() == iden:
                    selected = f
                    break
            if selected is None:
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools", "Error on selected"), level=Qgis.Critical,
                    duration=0
                )
                continue
            line_v2 = selected.geometry().constGet()
            if direction:
                rg = list(range(line_v2.numPoints()))
            else:
                rg = list(range(line_v2.numPoints()-1, -1, -1))
            rg_positions = []
            for i in rg:
                pt_v2 = line_v2.pointN(i)
                x = pt_v2.x()
                y = pt_v2.y()
                doublon = False
                for position in rg_positions:
                    if position['x'] == x and position['y'] == y and position['iden'] == iden:
                        self.__iface.messageBar().pushMessage(
                           QCoreApplication.translate("VDLTools", "Beware! the line ") + str(iden) +
                           QCoreApplication.translate("VDLTools", " has 2 identical summits on the vertex ") +
                           str(i-1) + QCoreApplication.translate("VDLTools", " same coordinates (X and Y). "
                                                                             "Please correct the line geometry."),
                           level=Qgis.Critical, duration=0
                        )
                        doublon = True
                        break
                for item in self.__points:
                    if item['x'] == x and item['y'] == y:
                        item['z'][num] = pt_v2.z()
                        rg_positions.append({'x': x, 'y': y, 'iden': iden})
                        doublon = True
                        break
                if not doublon:
                    rg_positions.append({'x': x, 'y': y, 'iden': iden})
                    z = []
                    for j in range(num_lines):
                        if j == num:
                            if pt_v2.z() == pt_v2.z():
                                z.append(pt_v2.z())
                            else:
                                z.append(0)
                        else:
                            z.append(None)
                    self.__points.append({'x': x, 'y': y, 'z': z})
                    if checkLayers:
                        for layer in availableLayers:
                            if layer in otherLayers:
                                continue
                            fs = Finder.findFeaturesAt(self.toMapCoordinates(layer, QgsPointXY(x, y)),
                                                       layer, self.SEARCH_TOLERANCE, QgsTolerance.LayerUnits, self)
                            if len(fs) > 0:
                                for f in fs:
                                    if layer == self.__lineLayer:
                                        if f.id() not in self.__selectedIds:
                                            vertex = f.geometry().closestVertex(QgsPoint(x, y))
                                            if vertex[4] < self.SEARCH_TOLERANCE:
                                                if layer not in otherLayers:
                                                    otherLayers.append(layer)
                                    elif layer not in otherLayers:
                                        otherLayers.append(layer)
            num += 1
        if checkLayers:
            return otherLayers

    def __onLayOk(self):
        """
        When the Ok button in Profile Layers Dialog is pushed
        """
        self.__layDlg.accept()
        self.__layers = self.__layDlg.getLayers()
        self.__usedMnts = self.__layDlg.getUsedMnts()
        self.__layOk()

    def __layOk(self):
        """
        To create the profile
        """
        self.__createProfile()
        self.__checkSituations()
        self.__isChoosed = False

    def __createProfile(self):
        """
        Create the profile in the dock
        """
        self.__features = []
        for points in self.__points:
            feat = []
            x = points['x']
            y = points['y']
            z = points['z']
            for layer in self.__layers:
                fs = Finder.findFeaturesAt(self.toMapCoordinates(layer, QgsPointXY(x, y)),
                                           layer, self.SEARCH_TOLERANCE, QgsTolerance.LayerUnits, self)
                if len(fs) == 0:
                    feat.append(None)
                    z.append(None)
                else:
                    feats = []
                    zs = []
                    for f in fs:
                        if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                            closest = f.geometry().closestVertex(QgsPointXY(x, y))
                            if closest[4] < self.SEARCH_TOLERANCE:
                                polygon_v2 = f.geometry().constGet()
                                zp = polygon_v2.vertexAt(ProfileTool.polygonVertexId(polygon_v2, closest[1])).z()
                                feats.append(f)
                                if zp is None or zp != zp:
                                    zs.append(0)
                                else:
                                    zs.append(zp)
                        elif layer.geometryType() == QgsWkbTypes.LineGeometry:
                            closest = f.geometry().closestVertex(QgsPointXY(x, y))
                            if closest[4] < self.SEARCH_TOLERANCE:
                                if layer == self.__lineLayer:
                                    if f.id() in self.__selectedIds:
                                        continue
                                feats.append(f)
                                line = f.geometry().constGet()
                                zp = line.zAt(closest[1])
                                if zp is None or zp != zp:
                                    zs.append(0)
                                else:
                                    zs.append(zp)
                        else:
                            zp = f.geometry().constGet().z()
                            feat.append(f)
                            if zp is None or zp != zp:
                                zs.append(0)
                            else:
                                zs.append(zp)

                    if len(zs) == 0:
                        z.append(None)
                    elif len(zs) == 1:
                        z.append(zs[0])
                    else:
                        z.append(zs)

                    if len(feats) == 0:
                        feat.append(None)
                    elif len(feats) == 1:
                        feat.append(feats[0])
                    else:
                        feat.append(feats)

            self.__features.append(feat)
        self.__calculateProfile()

    def __getNames(self):
        """
        To get the names from connected lines layers
        :return: the names list
        """
        names = [self.__lineLayer.name()]
        for layer in self.__layers:
            if layer.name() == self.__lineLayer.name():
                names.append(layer.name() + " conn.")
            else:
                names.append(layer.name())
        return names

    @staticmethod
    def __contains(line, point):
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
        """
        When keyboard is pressed
        :param event: keyboard event
        """
        if event.key() == Qt.Key_Escape:
            self.__cancel()

    def canvasMoveEvent(self, event):
        """
        When the mouse is moved
        :param event: mouse event
        """
        if not self.__isChoosed:
            if self.__lineLayer is not None:
                feat = Finder.findFeaturesAt(event.mapPoint(), self.__lineLayer, 10, QgsTolerance.Pixels, self)
                if not self.__inSelection:
                    if feat is not None and self.__lastFeatureId != feat.id():
                        self.__lastFeature = feat
                        self.__lastFeatureId = feat.id()
                        self.__lineLayer.setSelectedFeatures([feat.id()])
                    if feat is None:
                        self.__cancel()
                else:
                    if feat is not None and (self.__selectedIds is None or feat.id() not in self.__selectedIds):
                        line = feat.geometry().asPolyline()
                        if self.__contains(line, self.__endVertex) > -1:
                            self.__lastFeature = feat
                            self.__lastFeatureId = feat.id()
                            features = self.__selectedIds + [feat.id()]
                            self.__lineLayer.selectByIds(features)

                        elif self.__contains(line, self.__startVertex) > -1:
                            self.__lastFeature = feat
                            self.__lastFeatureId = feat.id()
                            features = self.__selectedIds + [feat.id()]
                            self.__lineLayer.selectByIds(features)

                        else:
                            self.__lineLayer.selectByIds(self.__selectedIds)
                            self.__lastFeatureId = None
                            self.__lastFeature = None

                if feat is None:
                    if self.__selectedIds is not None:
                        self.__lineLayer.selectByIds(self.__selectedIds)
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
            if self.__lineLayer.selectedFeatures() is not None and self.__selectedIds is not None:
                self.__isChoosed = True
                self.__setLayerDialog()
        elif event.button() == Qt.LeftButton:
            if self.__lastFeature is not None and \
                    (self.__selectedIds is None or self.__lastFeature.id() not in self.__selectedIds):
                self.__inSelection = True
                line = self.__lastFeature.geometry().asPolyline()
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools",
                                               "Select more lines with click left or process "
                                               "with click right (ESC to undo)"),
                    level=Qgis.Info, duration=3)
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
                    self.__lineLayer.selectByIds(self.__selectedIds)

    def __calculateProfile(self):
        """
        To calculate the profile and display it
        """
        if self.__points is None:
            return
        self.__dockWdg.clearData()
        if len(self.__points) == 0:
            return
        self.__dockWdg.setProfiles(self.__points, len(self.__selectedIds))
        self.__dockWdg.attachCurves(self.__getNames(), self.ownSettings, self.__usedMnts)

    def __checkSituations(self):
        """
        To check if point with no elevation on line, and one or more elevation from other layers,
        and if there are different elevations at the same point
        """
        situations = []
        differences = []
        for p in range(len(self.__points)):
            pt = self.__points[p]
            num_lines = len(self.__selectedIds)
            zz = []
            for i in range(num_lines):
                if pt['z'][i] is not None:
                    zz.append(i)
            if len(zz) == 0:
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools", "No line z ?!?"), level=Qgis.Warning)
            elif len(zz) == 1:
                z0 = pt['z'][zz[0]]
                for i in range(num_lines, len(pt['z'])):
                    if pt['z'][i] is None:
                        continue
                    if isinstance(pt['z'][i], list):
                        poz = 0
                        for z in pt['z'][i]:
                            if abs(z-z0) > self.ALT_TOLERANCE:
                                situations.append({'point': p, 'layer': (i-num_lines+1), 'vertex': z0, 'poz': poz})
                            poz += 1
                    else:
                        if abs(pt['z'][i]-z0) > self.ALT_TOLERANCE:
                            situations.append({'point': p, 'layer': (i-num_lines+1), 'vertex': z0})
            elif len(zz) == 2:
                z0 = pt['z'][zz[0]]
                if abs(pt['z'][zz[1]] - z0) > self.ALT_TOLERANCE:
                    differences.append({'point': p, 'v1': z0, 'v2': pt['z'][zz[1]]})
                else:
                    for i in range(num_lines, len(pt['z'])):
                        if pt['z'][i] is None:
                            continue
                        if isinstance(pt['z'][i], list):
                            for z in pt['z'][i]:
                                if abs(z-z0) > self.ALT_TOLERANCE:
                                    situations.append({'point': p, 'layer': (i-num_lines+1), 'vertex': z0})
                        else:
                            if abs(pt['z'][i]-z0) > self.ALT_TOLERANCE:
                                situations.append({'point': p, 'layer': (i-num_lines+1), 'vertex': z0})
            else:
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools", "More than 2 lines z ?!?"), level=Qgis.Warning)

        if (len(situations) > 0) or (len(differences) > 0):
            self.__setMessageDialog(situations, differences, self.__getNames())
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
            self.__checkZeros()

    @staticmethod
    def polygonVertexId(polygon_v2, vertex_id):
        """
        To get the id of the selected vertex from a polygon
        :param polygon_v2: the polygon as polygonV2
        :param vertex_id: selected vertex
        :return: id as QgsVertexId
        """
        eR = polygon_v2.exteriorRing()
        if vertex_id < eR.numPoints():
            return QgsVertexId(0, 0, vertex_id, 1)
        else:
            sel = vertex_id - eR.numPoints()
            for num in range(polygon_v2.numInteriorRings()):
                iR = polygon_v2.interiorRing(num)
                if sel < iR.numPoints():
                    return QgsVertexId(0, num + 1, sel, 1)
                sel -= iR.numPoints()
            return QgsVertexId()
