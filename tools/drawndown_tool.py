# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2018-08-21
        git sha              : $Format:%H$
        copyright            : (C) 2018 Ville de Lausanne
        author               : Ingénierie Informatique Gusthiot, Christophe Gusthiot
        email                : i2g@gusthiot.ch
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
from future.builtins import str
from future.builtins import range
from past.utils import old_div
from qgis.core import (QgsMapLayer,
                       QgsPointLocator,
                       QgsSnappingUtils,
                       QgsGeometry,
                       QGis,
                       QgsFeatureRequest,
                       QgsFeature,
                       QgsTolerance,
                       QgsPoint,
                       QgsWKBTypes
    )
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
from ..ui.profile_zeros_dialog import ProfileZerosDialog
from ..ui.drawdown_message_dialog import DrawdownMessageDialog


class DrawdownTool(QgsMapTool):
    """
    Tool class for
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
        self.icon_path = ':/plugins/VDLTools/icons/drawdown_icon.png'
        self.text = QCoreApplication.translate("VDLTools", "Drawdown")
        self.__lineLayer = None
        self.setCursor(Qt.ArrowCursor)
        self.__isChoosed = False
        self.__lastFeatureId = None
        self.__lastFeature = None
        self.__dockWdg = None
        # self.__layDlg = None
        # self.__msgDlg = None
        # self.__confDlg = None
        # self.__zeroDlg = None
        self.__adjDlg = None
        self.__points = None
        self.__layers = None
        self.__features = None
        self.__altitudes = None
        self.__inSelection = False
        self.__selectedIds = None
        self.__selectedStarts = None
        self.__selectedDirections = None
        self.__startVertex = None
        self.__endVertex = None
        # self.__rubberSit = None
        # self.__rubberDif = None
        self.ownSettings = None
        self.__usedMnts = None
        self.__isfloating = False
        self.__dockGeom = None
        self.__pipeDiam = None
        self.__refLayers = None
        self.__levelAtt = None
        self.__levelVal = None

    def setTool(self):
        """
        To set the current tool as this one
        """
        self.canvas().setMapTool(self)
        QMessageBox.information(
            None, QCoreApplication.translate("VDLTools", "Drawdown"),
            QCoreApplication.translate("VDLTools", "This tool is not yet finished, are you here to test it ?")
        )

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
        # self.__rubberSit = QgsRubberBand(self.canvas(), QGis.Point)
        # self.__rubberDif = QgsRubberBand(self.canvas(), QGis.Point)
        # color = QColor("red")
        # color.setAlphaF(0.78)
        # self.__rubberSit.setColor(color)
        # self.__rubberSit.setIcon(4)
        # self.__rubberSit.setIconSize(20)
        # self.__rubberDif.setColor(color)
        # self.__rubberDif.setIcon(2)
        # self.__rubberDif.setIconSize(20)
        self.__lineLayer = self.ownSettings.drawdownLayer
        self.__pipeDiam = self.ownSettings.pipeDiam
        self.__refLayers = self.ownSettings.refLayers
        self.__adjLayers = self.ownSettings.adjLayers
        self.__levelAtt = self.ownSettings.levelAtt
        self.__levelVal = self.ownSettings.levelVal

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
        # self.canvas().scene().removeItem(self.__rubberDif)
        # self.__rubberDif = None
        # self.canvas().scene().removeItem(self.__rubberSit)
        # self.__rubberSit = None
        if self.__dockWdg is not None:
            self.__dockWdg.close()
        QgsMapTool.deactivate(self)

    def __cancel(self):
        """
        To cancel used variables
        """
        if self.__lineLayer is not None:
            self.__lineLayer.removeSelection()
        self.__isChoosed = False
        self.__lastFeatureId = None
        self.__lastFeature = None
        self.__selectedIds = None
        self.__selectedDirections = None
        self.__startVertex = None
        self.__endVertex = None
        self.__inSelection = False
        # self.__layDlg = None
        # self.__msgDlg = None
        # self.__confDlg = None
        # self.__zeroDlg = None
        self.__adjDlg = None

    def setEnable(self):
        """
        To check if we can enable the action for the selected layer
        :param layer: selected layer
        """
        enable = True
        if self.ownSettings is None or self.ownSettings.refLayers is None or len(self.ownSettings.refLayers) == 0 \
                or self.ownSettings.levelAtt is None or self.ownSettings.levelVal is None \
                or self.ownSettings.levelVal == "" or self.ownSettings.drawdownLayer is None \
                or self.ownSettings.pipeDiam is None:
            enable = False

        if enable:
            self.action().setEnabled(True)
        else:
            self.action().setEnabled(False)
            if self.canvas().mapTool() == self:
                self.__iface.actionPan().trigger()
            if self.__dockWdg is not None:
                self.__dockWdg.close()
            self.__lineLayer = None
        return

    def __adjust(self):
        self.__layers = self.__lineVertices(True)
        adjustments = []
        self.__altitudes = []
        self.__features = []

        for p in range(len(self.__points)):
            feat = []
            pt = self.__points[p]
            num_lines = len(self.__selectedIds)
            drawdown = False
            level = None
            lay_name = None
            for layer in self.__refLayers:
                laySettings = QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Vertex, self.SEARCH_TOLERANCE,
                                                           QgsTolerance.LayerUnits)
                f_l = Finder.findClosestFeatureAt(self.toMapCoordinates(layer, QgsPoint(pt['x'], pt['y'])),
                                                  self.canvas(), [laySettings])
                if f_l is not None:
                    feature = f_l[0]
                    lay_name = f_l[1].name()
                    point_v2 = GeometryV2.asPointV2(feature.geometry(), self.__iface)
                    if level is not None:
                        if (level - point_v2.z()) > 0.005:
                            self.__iface.messageBar().pushMessage(
                                QCoreApplication.translate(
                                    "VDLTools", "More than one reference point, with 2 different elevations !!"),
                                level=QgsMessageBar.CRITICAL, duration=0)
                            self.__cancel()
                            return
                    level = point_v2.z()
                    if str(feature.attribute(self.__levelAtt)) == self.__levelVal:
                        drawdown = True
                    # print(lay_name, level, drawdown)
            diam = 0
            for i in range(num_lines):
                if pt['z'][i] is None:
                    continue
                id = self.__selectedIds[i]
                feature = QgsFeature()
                self.__lineLayer.getFeatures(QgsFeatureRequest().setFilterFid(id)).nextFeature(feature)
                dtemp = feature.attribute(self.__pipeDiam)/1000
                if dtemp > diam:
                    diam = dtemp
                selected = None
                for f in self.__lineLayer.selectedFeatures():
                    if f.id() == id:
                        selected = f
                        break
                adjustments.append({'point': p, 'previous': pt['z'][i], 'line': True, 'layer': self.__lineLayer,
                                    'feature': selected})

            for layer in self.__layers:
                laySettings = QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Vertex, self.SEARCH_TOLERANCE,
                                                           QgsTolerance.LayerUnits)
                f_l = Finder.findClosestFeatureAt(self.toMapCoordinates(layer, QgsPoint(pt['x'], pt['y'])),
                                                  self.canvas(), [laySettings])

                z = pt['z']
                if f_l is None:
                    feat.append(None)
                    z.append(None)
                else:
                    zp = GeometryV2.asPointV2(f_l[0].geometry(), self.__iface).z()
                    feat.append(f_l[0])
                    if zp is None or zp != zp:
                        zp = 0
                    z.append(zp)
                    adjustments.append({'point': p, 'previous': zp, 'line': False,
                                        'layer': f_l[1], 'feature': f_l[0]})

            self.__features.append(feat)

            if level is not None:
                if drawdown:
                    alt = level - diam
                else:
                    alt = level
            else:
                alt = None

            self.__altitudes.append({'diam': diam, 'drawdown': drawdown, 'alt': alt, 'layer': lay_name})

        last = len(self.__altitudes)-1
        for i in range(len(self.__altitudes)):
            if self.__altitudes[i]['alt'] is None:
                if 0 < i < last:
                    prev_alt = self.__altitudes[i-1]['alt']
                    next_alt = self.__altitudes[i+1]['alt']
                    if prev_alt is not None and next_alt is not None:
                        prev_pt = self.__points[i-1]
                        next_pt = self.__points[i+1]
                        pt = self.__points[i]
                        d0 = Finder.sqrDistForCoords(pt['x'], prev_pt['x'], pt['y'], prev_pt['y'])
                        d1 = Finder.sqrDistForCoords(next_pt['x'], pt['x'], next_pt['x'], pt['x'])
                        inter_alt = old_div((d0*next_alt + d1*prev_alt), (d0 + d1))
                        self.__altitudes[i]['alt'] = inter_alt
                        self.__altitudes[i]['drawdown'] = "interpolated"
                elif i == 0 and len(self.__altitudes) > 2:
                    alt1 = self.__altitudes[1]['alt']
                    alt2 = self.__altitudes[2]['alt']
                    if alt1 is not None and alt2 is not None:
                        pt2 = self.__points[2]
                        pt1 = self.__points[1]
                        pt = self.__points[0]
                        big_d = Finder.sqrDistForCoords(pt2['x'], pt1['x'], pt2['y'], pt1['y'])
                        small_d = Finder.sqrDistForCoords(pt1['x'], pt['x'], pt1['y'], pt['y'])
                        if small_d < (old_div(big_d, 4)):
                            self.__altitudes[i]['alt'] = alt2 + (1 + old_div(small_d, big_d)) * (alt1 - alt2)
                            self.__altitudes[i]['drawdown'] = "extrapolated"
                        else:
                            self.__altitudes[i]['drawdown'] = "cannot be extrapolated"
                elif i == last and len(self.__altitudes) > 2:
                    alt1 = self.__altitudes[i-1]['alt']
                    alt2 = self.__altitudes[i-2]['alt']
                    if alt1 is not None and alt2 is not None:
                        pt2 = self.__points[i-2]
                        pt1 = self.__points[i-1]
                        pt = self.__points[i]
                        big_d = Finder.sqrDistForCoords(pt2['x'], pt1['x'], pt2['y'], pt1['y'])
                        small_d = Finder.sqrDistForCoords(pt1['x'], pt['x'], pt1['y'], pt['y'])
                        if small_d < (old_div(big_d, 4)):
                            self.__altitudes[i]['alt'] = alt2 + (1 + old_div(small_d, big_d)) * (alt1 - alt2)
                            self.__altitudes[i]['drawdown'] = "extrapolated"
                        else:
                            self.__altitudes[i]['drawdown'] = "cannot be extrapolated"

        self.__adjDlg = DrawdownMessageDialog(adjustments, self.__altitudes)
        self.__adjDlg.rejected.connect(self.__cancel)
        self.__adjDlg.cancelButton().clicked.connect(self.__onAdjCancel)
        self.__adjDlg.applyButton().clicked.connect(self.__onAdjOk)
        self.__adjDlg.show()

    def __onAdjOk(self):
        self.__adjDlg.accept()
        adjustements = self.__adjDlg.getAdjusts()
        lines = {}
        for adj in adjustements:
            if self.__altitudes[adj['point']]['alt'] is None:
                continue
            if adj['line']:
                id = adj['feature'].id()
                if id not in lines:
                    line_v2, curved = GeometryV2.asLineV2(adj['feature'].geometry(), self.__iface)
                    lines[id] = line_v2
                line = lines[id]

                num_lines = len(self.__selectedIds)
                for i in range(num_lines):
                    if self.__points[adj['point']]['z'][i] is not None:
                        index = adj['point']-self.__selectedStarts[i]
                        if not self.__selectedDirections[i]:
                            index = line.numPoints()-1-index
                        line.setZAt(index, self.__altitudes[adj['point']]['alt'])
            else:
                pt = adj['point']
                self.__changePoint(adj['layer'], adj['feature'], self.__altitudes[pt]['alt'])
        if not self.__lineLayer.isEditable():
            self.__lineLayer.startEditing()
        for key, line in lines.items():
            geom = QgsGeometry(line.clone())
            self.__lineLayer.changeGeometry(key, geom)
        self.__calculateProfile()
        self.__cancel()


    def __onAdjCancel(self):
        self.__adjDlg.reject()
        self.__cancel()

    def __changePoint(self, layer, feat, newZ):
        """
        To change Vertex elevation
        :param layer: layer containing the object
        :param feat: QgsFeature of the object
        :param newZ: new elevation
        """
        feat_v2 = GeometryV2.asPointV2(feat.geometry(), self.__iface)
        feat_v2.setZ(newZ)
        if not layer.isEditable():
            layer.startEditing()
        layer.changeGeometry(feat.id(), QgsGeometry(feat_v2))

    # def __setLayerDialog(self):
    #     """
    #     To create a Profile Layers Dialog
    #     """
    #     otherLayers = self.__lineVertices(True)
        # with_mnt = True
        # if self.ownSettings is None or self.ownSettings.mntUrl is None \
        #         or self.ownSettings.mntUrl == "":
        #     with_mnt = False
        # if not with_mnt and len(otherLayers) == 0:
        #     self.__layers = []
        #     self.__layOk()
        # else:
        #     self.__layDlg = ProfileLayersDialog(otherLayers, with_mnt)
        #     self.__layDlg.rejected.connect(self.__cancel)
        #     self.__layDlg.okButton().clicked.connect(self.__onLayOk)
        #     self.__layDlg.cancelButton().clicked.connect(self.__onLayCancel)
        #     self.__layDlg.show()

    # def __setMessageDialog(self, situations, differences, names):
    #     """
    #     To create a Profile Message Dialog
    #     :param situations: elevation differences between line and points
    #     :param differences: elevation differences between lines
    #     :param names: layers names
    #     """
    #     self.__msgDlg = ProfileMessageDialog(situations, differences, names, self.__points)
    #     self.__msgDlg.rejected.connect(self.__checkZeros)
    #     self.__msgDlg.passButton().clicked.connect(self.__onMsgPass)
    #     self.__msgDlg.onLineButton().clicked.connect(self.__onMsgLine)
    #     self.__msgDlg.onPointsButton().clicked.connect(self.__onMsgPoints)
    #
    # def __setConfirmDialog(self, origin):
    #     """
    #     To create a Profile Confirm Dialog
    #     :param origin: '0' if we copy points elevations to line, '1' if we copy line elevation to points
    #     """
    #     self.__confDlg = ProfileConfirmDialog()
    #     if origin == 0 and not self.__lineLayer.isEditable():
    #         self.__confDlg.setMessage(
    #             QCoreApplication.translate("VDLTools", "Do you really want to edit the LineString layer ?"))
    #         self.__confDlg.rejected.connect(self.__checkZeros)
    #         self.__confDlg.okButton().clicked.connect(self.__onConfirmLine)
    #         self.__confDlg.cancelButton().clicked.connect(self.__onConfirmCancel)
    #         self.__confDlg.show()
    #     elif origin != 0:
    #         situations = self.__msgDlg.getSituations()
    #         case = True
    #         for s in situations:
    #             layer = self.__layers[s['layer'] - 1]
    #             if not layer.isEditable():
    #                 case = False
    #                 break
    #         if not case:
    #             self.__confDlg.setMessage(
    #                 QCoreApplication.translate("VDLTools", "Do you really want to edit the Point layer(s) ?"))
    #             self.__confDlg.rejected.connect(self.__checkZeros)
    #             self.__confDlg.okButton().clicked.connect(self.__onConfirmPoints)
    #             self.__confDlg.cancelButton().clicked.connect(self.__onConfirmCancel)
    #             self.__confDlg.show()
    #         else:
    #             self.__confirmPoints()
    #     else:
    #         self.__confirmLine()

    # def __getOtherLayers(self):
    #     """
    #     To get all points layers that can be used
    #     :return: layers list
    #     """
    #     layerList = []
    #     types = [QgsWKBTypes.PointZ, QgsWKBTypes.LineStringZ, QgsWKBTypes.CircularStringZ, QgsWKBTypes.CompoundCurveZ,
    #              QgsWKBTypes.CurvePolygonZ, QgsWKBTypes.PolygonZ]
    #     for layer in self.canvas().layers():
    #         if layer.type() == QgsMapLayer.VectorLayer and QGis.fromOldWkbType(layer.wkbType()) in types:
    #             if layer not in self.__refLayers:
    #                 layerList.append(layer)
    #     return layerList

    # def __onMsgPass(self):
    #     """
    #     When the Pass button in Profile Message Dialog is pushed
    #     """
    #     self.__msgDlg.reject()
    #
    # def __onConfirmCancel(self):
    #     """
    #     When the Cancel button in Profile Confirm Dialog is pushed
    #     """
    #     self.__confDlg.reject()
    #
    # def __onMsgLine(self):
    #     """
    #     When the Line button in Profile Message Dialog is pushed
    #     """
    #     self.__setConfirmDialog(0)
    #
    # def __onMsgPoints(self):
    #     """
    #     When the Points button in Profile Message Dialog is pushed
    #     """
    #     self.__setConfirmDialog(1)
    #
    # def __onConfirmLine(self):
    #     """
    #     When the Line button in Profile Confirm Dialog is pushed
    #     """
    #     self.__confDlg.accept()
    #     self.__confirmLine()
    #
    # def __checkZeros(self):
    #     """
    #     To check if there are zeros in selected objects
    #     """
    #     alts = []
    #     nb_not_none = []
    #     for i in range(len(self.__points)):
    #         zz = self.__points[i]['z']
    #         alt = 0
    #         nb = 0
    #         for z in zz:
    #             if z is not None:
    #                 nb += 1
    #                 if z > alt:
    #                     alt = z
    #         alts.append(alt)
    #         nb_not_none.append(nb)
    #
    #     zeros = []
    #     for i in range(len(self.__points)):
    #         if alts[i] == 0:
    #             if i == 0:
    #                 ap = None
    #                 app = None
    #                 j = 1
    #                 while True:
    #                     if i+j > len(self.__points)-1:
    #                         break
    #                     if alts[i+j] != 0:
    #                         ap = j
    #                         j += 1
    #                         while True:
    #                             if i+j > len(self.__points)-1:
    #                                 break
    #                             if alts[i+j] != 0:
    #                                 app = j
    #                                 break
    #                             j += 1
    #                         break
    #                     j += 1
    #                 if ap is None or app is None:
    #                     zeros.append([i, None, None])
    #                 else:
    #                     big_d = Finder.sqrDistForCoords(self.__points[ap]['x'], self.__points[app]['x'],
    #                                                     self.__points[ap]['y'], self.__points[app]['y'])
    #                     small_d = Finder.sqrDistForCoords(self.__points[i]['x'], self.__points[ap]['x'],
    #                                                       self.__points[i]['y'], self.__points[ap]['y'])
    #                     if small_d < (old_div(big_d, 4)):
    #                         zextra = alts[app] + (1 + old_div(small_d, big_d)) * (alts[ap] - alts[app])
    #                         zeros.append([i, zextra, nb_not_none[i]])
    #                     else:
    #                         zeros.append([i, None, None])
    #             elif i == len(self.__points)-1:
    #                 av = None
    #                 avv = None
    #                 j = 1
    #                 while True:
    #                     if i-j < 0:
    #                         break
    #                     if alts[i-j] != 0:
    #                         av = j
    #                         j += 1
    #                         while True:
    #                             if i-j < 0:
    #                                 break
    #                             if alts[i-j] != 0:
    #                                 avv = j
    #                                 break
    #                             j += 1
    #                         break
    #                     j += 1
    #                 if av is None or avv is None:
    #                     zeros.append([i, None, None])
    #                 else:
    #                     big_d = Finder.sqrDistForCoords(self.__points[i-av]['x'], self.__points[i-avv]['x'],
    #                                                     self.__points[i-av]['y'], self.__points[i-avv]['y'])
    #                     small_d = Finder.sqrDistForCoords(self.__points[i]['x'], self.__points[i-av]['x'],
    #                                                       self.__points[i]['y'], self.__points[i-av]['y'])
    #                     if small_d < (old_div(big_d, 4)):
    #                         zextra = alts[i-avv] + (1 + old_div(small_d, big_d)) * (alts[i-av] - alts[i-avv])
    #                         zeros.append([i, zextra, nb_not_none[i]])
    #                     else:
    #                         zeros.append([i, None, None])
    #             else:
    #                 av = None
    #                 j = 1
    #                 while True:
    #                     if i-j < 0:
    #                         break
    #                     if alts[i-j] != 0:
    #                         av = j
    #                         break
    #                     j += 1
    #                 ap = None
    #                 j = 1
    #                 while True:
    #                     if i+j > len(self.__points)-1:
    #                         break
    #                     if alts[i+j] != 0:
    #                         ap = j
    #                         break
    #                     j += 1
    #                 if av is None or ap is None:
    #                     zeros.append([i, None, None])
    #                 else:
    #                     d0 = Finder.sqrDistForCoords(
    #                         self.__points[i-av]['x'], self.__points[i]['x'], self.__points[i-av]['y'],
    #                         self.__points[i]['y'])
    #                     d1 = Finder.sqrDistForCoords(
    #                         self.__points[i+ap]['x'], self.__points[i]['x'], self.__points[i+ap]['y'],
    #                         self.__points[i]['y'])
    #                     zinter = old_div((d0*alts[i+ap] + d1*alts[i-av]), (d0 + d1))
    #                     zeros.append([i, zinter, nb_not_none[i]])
    #     if len(zeros) > 0:
    #         self.__zeroDlg = ProfileZerosDialog(zeros)
    #         self.__zeroDlg.rejected.connect(self.__cancel)
    #         self.__zeroDlg.passButton().clicked.connect(self.__onZeroPass)
    #         self.__zeroDlg.applyButton().clicked.connect(self.__onZeroApply)
    #         self.__zeroDlg.show()
    #     else:
    #         self.__cancel()
    #
    # def __onZeroPass(self):
    #     """
    #     When the Pass button in Profile Zeros Dialog is pushed
    #     """
    #     self.__zeroDlg.reject()
    #
    # def __onZeroApply(self):
    #     """
    #     When the Apply button in Profile Zeros Dialog is pushed
    #     """
    #     self.__zeroDlg.accept()
    #     zeros = self.__zeroDlg.getZeros()
    #
    #     num_lines = len(self.__selectedIds)
    #     lines = []
    #     for iden in self.__selectedIds:
    #         for f in self.__lineLayer.selectedFeatures():
    #             if f.id() == iden:
    #                 line, curved = GeometryV2.asLineV2(f.geometry(), self.__iface)
    #                 lines.append(line)
    #                 break
    #     for z in zeros:
    #         for i in range(num_lines):
    #             if self.__points[z[0]]['z'][i] is not None:
    #                 index = z[0]-self.__selectedStarts[i]
    #                 if not self.__selectedDirections[i]:
    #                     index = lines[i].numPoints()-1-index
    #                 lines[i].setZAt(index, z[1])
    #         if z[2] > 1:
    #             zz = self.__points[z[0]]['z']
    #             for p in range(len(zz)-num_lines):
    #                 if zz[num_lines+p] is not None:
    #                     feat = self.__features[z[0]][p]
    #                     layer = self.__layers[p]
    #                     self.__changePoint(layer, z[0], feat, z[1])
    #     if not self.__lineLayer.isEditable():
    #         self.__lineLayer.startEditing()
    #     for i in range(len(lines)):
    #         geom = QgsGeometry(lines[i].clone())
    #         self.__lineLayer.changeGeometry(self.__selectedIds[i], geom)
    #         # self.__lineLayer.updateExtents()
    #     self.__dockWdg.clearData()
    #     self.__lineVertices()
    #     self.__createProfile()
    #     self.__cancel()
    #
    # def __confirmLine(self):
    #     """
    #     To change the elevations of some vertices of the line
    #     """
    #     situations = self.__msgDlg.getSituations()
    #     num_lines = len(self.__selectedIds)
    #     points = {}
    #     for s in situations:
    #         if s['point'] not in points:
    #             points[s['point']] = self.__points[s['point']]['z'][s['layer']+num_lines-1]
    #         else:
    #             diff = abs(self.__points[s['point']]['z'][s['layer']+num_lines-1] - points[s['point']])
    #             if diff > 0.001:
    #                 QMessageBox.information(
    #                     None, QCoreApplication.translate("VDLTools", "Elevation"),
    #                     QCoreApplication.translate("VDLTools", "There is more than one elevation for the point ") +
    #                     str(s['point'])
    #                 )
    #                 return
    #     self.__msgDlg.accept()
    #     lines = []
    #     for iden in self.__selectedIds:
    #         for f in self.__lineLayer.selectedFeatures():
    #             if f.id() == iden:
    #                 line, curved = GeometryV2.asLineV2(f.geometry(), self.__iface)
    #                 lines.append(line)
    #                 break
    #     for s in situations:
    #         z = self.__points[s['point']]['z'][s['layer']+num_lines-1]
    #         for i in range(num_lines):
    #             if self.__points[s['point']]['z'][i] is not None:
    #                 index = s['point']-self.__selectedStarts[i]
    #                 if not self.__selectedDirections[i]:
    #                     index = lines[i].numPoints()-1-index
    #                 lines[i].setZAt(index, z)
    #     if not self.__lineLayer.isEditable():
    #         self.__lineLayer.startEditing()
    #     for i in range(len(lines)):
    #         geom = QgsGeometry(lines[i].clone())
    #         self.__lineLayer.changeGeometry(self.__selectedIds[i], geom)
    #     self.__dockWdg.clearData()
    #     self.__lineVertices()
    #     self.__createProfile()
    #     self.__checkZeros()
    #
    # def __onConfirmPoints(self):
    #     """
    #     When the Points button in Profile Confirm Dialog is pushed
    #     """
    #     self.__confDlg.accept()
    #     self.__confirmPoints()
    #
    # def __confirmPoints(self):
    #     """
    #     To change the elevations of certain points
    #     """
    #     self.__msgDlg.accept()
    #     situations = self.__msgDlg.getSituations()
    #     num_lines = len(self.__selectedIds)
    #     for s in situations:
    #         layer = self.__layers[s['layer']-1]
    #         feat = self.__features[s['point']][s['layer']-1]
    #         newZ = 0
    #         for i in range(num_lines):
    #             if self.__points[s['point']]['z'][i] is not None:
    #                 newZ = self.__points[s['point']]['z'][i]
    #                 break
    #         self.__changePoint(layer, s['point'], feat, newZ)
    #     self.__dockWdg.clearData()
    #     self.__lineVertices()
    #     self.__createProfile()
    #     self.__checkZeros()
    #
    # def __changePoint(self, layer, pos, feat, newZ):
    #     """
    #     To change Vertex elevation
    #     :param layer: layer containing the object
    #     :param pos: vertex position in the object (if not a point)
    #     :param feat: QgsFeature of the object
    #     :param newZ: new elevation
    #     """
    #     if layer.geometryType() == QGis.Polygon:
    #         closest = feat.geometry().closestVertex(
    #             QgsPoint(self.__points[pos]['x'], self.__points[pos]['y']))
    #         feat_v2, curved = GeometryV2.asPolygonV2(feat.geometry(), self.__iface)
    #         position = GeometryV2.polygonVertexId(feat_v2, closest[1])
    #         vertex = feat_v2.vertexAt(position)
    #         feat_v2.deleteVertex(position)
    #         vertex.setZ(newZ)
    #         feat_v2.insertVertex(position, vertex)
    #     elif layer.geometryType() == QGis.Line:
    #         closest = feat.geometry().closestVertex(
    #             QgsPoint(self.__points[pos]['x'], self.__points[pos]['y']))
    #         feat_v2, curved = GeometryV2.asLineV2(feat.geometry(), self.__iface)
    #         feat_v2.setZAt(closest[1], newZ)
    #     else:
    #         feat_v2 = GeometryV2.asPointV2(feat.geometry(), self.__iface)
    #         feat_v2.setZ(newZ)
    #     if not layer.isEditable():
    #         layer.startEditing()
    #     layer.changeGeometry(feat.id(), QgsGeometry(feat_v2))

    # def __onLayCancel(self):
    #     """
    #     When the Cancel button in Profile Layers Dialog is pushed
    #     """
    #     self.__layDlg.reject()
    #     self.__isChoosed = False

    def __lineVertices(self, checkLayers=False):
        """
        To check if vertices of others layers are crossing the displaying line
        :param checkLayers: if we want to get the list of the other layers in return
        :return: other layers list if requested
        """
        if checkLayers:
            # availableLayers = self.__getOtherLayers()
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
                    QCoreApplication.translate("VDLTools", "Error on selected"), level=QgsMessageBar.CRITICAL,
                    duration=0
                )
                continue
            line_v2, curved = GeometryV2.asLineV2(selected.geometry(), self.__iface)
            if direction:
                rg = range(line_v2.numPoints())
            else:
                rg = range(line_v2.numPoints()-1, -1, -1)
            rg_positions = []
            for i in rg:
                pt_v2 = line_v2.pointN(i)
                x = pt_v2.x()
                y = pt_v2.y()
                doublon = False
                for position in rg_positions:
                    if position['x'] == x and position['y'] == y:
                        self.__iface.messageBar().pushMessage(
                           QCoreApplication.translate("VDLTools", "Beware! the line ") + str(iden) +
                           QCoreApplication.translate("VDLTools", " has 2 identical summits on the vertex ") +
                           str(i-1) + QCoreApplication.translate("VDLTools", " same coordinates (X and Y). "
                                                                             "Please correct the line geometry."),
                           level=QgsMessageBar.CRITICAL, duration=0
                        )
                        doublon = True
                        break
                for item in self.__points:
                    if item['x'] == x and item['y'] == y:
                        item['z'][num] = pt_v2.z()
                        doublon = True
                        break
                if not doublon:
                    rg_positions.append({'x': x, 'y': y})
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
                        for layer in self.__adjLayers:
                            if layer in otherLayers:
                                continue
                            laySettings = QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Vertex, self.SEARCH_TOLERANCE,
                                                                       QgsTolerance.LayerUnits)
                            f_l = Finder.findClosestFeatureAt(self.toMapCoordinates(layer, QgsPoint(x, y)),
                                                              self.canvas(), [laySettings])

                            if f_l is not None:
                                if layer == self.__lineLayer:
                                    other = False
                                    if f_l[0].id() not in self.__selectedIds:
                                        other = True
                                    else:
                                        fs = Finder.findFeaturesAt(QgsPoint(x, y), laySettings, self)
                                        for f in fs:
                                            if f.id() not in self.__selectedIds:
                                                vertex = f.geometry().closestVertex(QgsPoint(x, y))
                                                if vertex[4] < self.SEARCH_TOLERANCE:
                                                    other = True
                                                    break
                                    if other and layer not in otherLayers:
                                        otherLayers.append(layer)
                                elif layer not in otherLayers:
                                    otherLayers.append(layer)
            num += 1
        if checkLayers:
            return otherLayers

    # def __onLayOk(self):
    #     """
    #     When the Ok button in Profile Layers Dialog is pushed
    #     """
    #     self.__layDlg.accept()
    #     self.__layers = self.__layDlg.getLayers()
    #     self.__usedMnts = self.__layDlg.getUsedMnts()
    #     self.__layOk()

    # def __layOk(self):
    #     """
    #     To create the profile
    #     """
    #     self.__createProfile()
    #     self.__checkSituations()
    #     self.__isChoosed = False
    #
    # def __createProfile(self):
    #     """
    #     Create the profile in the dock
    #     """
    #     self.__features = []
    #
    #     for points in self.__points:
    #         feat = []
    #         x = points['x']
    #         y = points['y']
    #         z = points['z']
    #         for layer in self.__layers:
    #             laySettings = QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Vertex, self.SEARCH_TOLERANCE,
    #                                                        QgsTolerance.LayerUnits)
    #             f_l = Finder.findClosestFeatureAt(self.toMapCoordinates(layer, QgsPoint(x, y)), self.canvas(),
    #                                               [laySettings])
    #             if f_l is None:
    #                 feat.append(None)
    #                 z.append(None)
    #             else:
    #                 if f_l[1].geometryType() == QGis.Polygon:
    #                     closest = f_l[0].geometry().closestVertex(QgsPoint(x, y))
    #                     polygon_v2, curved = GeometryV2.asPolygonV2(f_l[0].geometry(), self.__iface)
    #                     zp = polygon_v2.vertexAt(GeometryV2.polygonVertexId(polygon_v2, closest[1])).z()
    #                     feat.append(f_l[0])
    #                     if zp is None or zp != zp:
    #                         z.append(0)
    #                     else:
    #                         z.append(zp)
    #                 elif f_l[1].geometryType() == QGis.Line:
    #                     f_ok = None
    #                     if layer == self.__lineLayer:
    #                         if f_l[0].id() not in self.__selectedIds:
    #                             f_ok = f_l[0]
    #                         else:
    #                             fs = Finder.findFeaturesAt(QgsPoint(x, y), laySettings, self)
    #                             for f in fs:
    #                                 if f.id() not in self.__selectedIds:
    #                                     vertex = f.geometry().closestVertex(QgsPoint(x, y))
    #                                     if vertex[4] < self.SEARCH_TOLERANCE:
    #                                         f_ok = f
    #                                         break
    #                     else:
    #                         f_ok = f_l[0]
    #                     if f_ok is not None:
    #                         closest = f_ok.geometry().closestVertex(QgsPoint(x, y))
    #                         feat.append(f_ok)
    #                         line, curved = GeometryV2.asLineV2(f_ok.geometry(), self.__iface)
    #                         zp = line.zAt(closest[1])
    #                         if zp is None or zp != zp:
    #                             z.append(0)
    #                         else:
    #                             z.append(zp)
    #                     else:
    #                         feat.append(None)
    #                         z.append(None)
    #                 else:
    #                     zp = GeometryV2.asPointV2(f_l[0].geometry(), self.__iface).z()
    #                     feat.append(f_l[0])
    #                     if zp is None or zp != zp:
    #                         z.append(0)
    #                     else:
    #                         z.append(zp)
    #         self.__features.append(feat)
    #     self.__calculateProfile()
    #
    def __getNames(self):
        """
        To get the names from connected lines layers
        :return: the names list
        """
        names = [self.__lineLayer.name()]
        for layer in self.__layers:
            # if layer.name() == self.__lineLayer.name():
            #     names.append(layer.name() + QCoreApplication.translate("VDLTools", " connected"))
            # else:
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
                laySettings = QgsSnappingUtils.LayerConfig(self.__lineLayer, QgsPointLocator.All, 10,
                                                           QgsTolerance.Pixels)
                f_l = Finder.findClosestFeatureAt(event.mapPoint(), self.canvas(), [laySettings])
                if not self.__inSelection:
                    if f_l is not None and self.__lastFeatureId != f_l[0].id():
                        self.__lastFeature = f_l[0]
                        self.__lastFeatureId = f_l[0].id()
                        self.__lineLayer.setSelectedFeatures([f_l[0].id()])
                    if f_l is None:
                        self.__cancel()
                else:
                    if f_l is not None and (self.__selectedIds is None or f_l[0].id() not in self.__selectedIds):
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
                    if self.__selectedIds is not None:
                        self.__lineLayer.setSelectedFeatures(self.__selectedIds)
                    self.__lastFeatureId = None
                    self.__lastFeature = None

    def canvasReleaseEvent(self, event):
        """
        When the mouse is clicked
        :param event: mouse event
        """
        # self.__rubberSit.reset()
        # self.__rubberDif.reset()
        if event.button() == Qt.RightButton:
            if self.__lineLayer.selectedFeatures() is not None and self.__selectedIds is not None:
                self.__isChoosed = True
                self.__adjust()
                # self.__setLayerDialog()
        elif event.button() == Qt.LeftButton:
            if self.__lastFeature is not None and \
                    (self.__selectedIds is None or self.__lastFeature.id() not in self.__selectedIds):
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
    #
    # def __checkSituations(self):
    #     """
    #     To check if point with no elevation on line, and one or more elevation from other layers,
    #     and if there are different elevations at the same point
    #     """
    #     situations = []
    #     differences = []
    #     for p in range(len(self.__points)):
    #         pt = self.__points[p]
    #         num_lines = len(self.__selectedIds)
    #         zz = []
    #         for i in range(num_lines):
    #             if pt['z'][i] is not None:
    #                 zz.append(i)
    #         if len(zz) == 0:
    #             self.__iface.messageBar().pushMessage(
    #                 QCoreApplication.translate("VDLTools", "No line z ?!?"), level=QgsMessageBar.WARNING)
    #         elif len(zz) == 1:
    #             z0 = pt['z'][zz[0]]
    #             for i in range(num_lines, len(pt['z'])):
    #                 if pt['z'][i] is None:
    #                     continue
    #                 if abs(pt['z'][i]-z0) > self.ALT_TOLERANCE:
    #                     situations.append({'point': p, 'layer': (i-num_lines+1), 'vertex': z0})
    #         elif len(zz) == 2:
    #             z0 = pt['z'][zz[0]]
    #             if abs(pt['z'][zz[1]] - z0) > self.ALT_TOLERANCE:
    #                 differences.append({'point': p, 'v1': z0, 'v2': pt['z'][zz[1]]})
    #             else:
    #                 for i in range(num_lines, len(pt['z'])):
    #                     if pt['z'][i] is None:
    #                         continue
    #                     if abs(pt['z'][i]-z0) > self.ALT_TOLERANCE:
    #                         situations.append({'point': p, 'layer': (i-num_lines+1), 'vertex': z0})
    #         else:
    #             self.__iface.messageBar().pushMessage(
    #                 QCoreApplication.translate("VDLTools", "More than 2 lines z ?!?"), level=QgsMessageBar.WARNING)
    #
    #     if (len(situations) > 0) or (len(differences) > 0):
    #         self.__setMessageDialog(situations, differences, self.__getNames())
    #         self.__rubberSit.reset()
    #         self.__rubberDif.reset()
    #         for situation in situations:
    #             pt = self.__points[situation['point']]
    #             point = QgsPoint(pt['x'], pt['y'])
    #             if self.__rubberSit.numberOfVertices() == 0:
    #                 self.__rubberSit.setToGeometry(QgsGeometry().fromPoint(point), None)
    #             else:
    #                 self.__rubberSit.addPoint(point)
    #         for difference in differences:
    #             pt = self.__points[difference['point']]
    #             point = QgsPoint(pt['x'], pt['y'])
    #             if self.__rubberDif.numberOfVertices() == 0:
    #                 self.__rubberDif.setToGeometry(QgsGeometry().fromPoint(point), None)
    #             else:
    #                 self.__rubberDif.addPoint(point)
    #
    #         self.__msgDlg.show()
    #     else:
    #         self.__checkZeros()
