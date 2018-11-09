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
from qgis.core import (QgsPointLocator,
                       QgsSnappingUtils,
                       QgsGeometry,
                       QgsFeatureRequest,
                       QgsFeature,
                       QgsTolerance,
                       QgsPoint
    )
from qgis.gui import (QgsMapTool,
                      QgsMessageBar)
from PyQt4.QtCore import (Qt,
                          QCoreApplication)
from PyQt4.QtGui import QMessageBox
from ..core.finder import Finder
from ..core.geometry_v2 import GeometryV2
from ..ui.profile_dock_widget import ProfileDockWidget
from ..ui.drawdown_adjustment_dialog import DrawdownAdjustmentDialog
from ..ui.drawdown_edition_dialog import DrawdownEditionDialog
from ..ui.drawdown_confirm_dialog import DrawdownConfirmDialog


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
        self.setCursor(Qt.ArrowCursor)
        self.__isChoosed = False
        self.__lastFeatureId = None
        self.__lastFeature = None
        self.__dockWdg = None
        self.__adjDlg = None
        self.__editDlg = None
        self.__confDlg = None
        self.__points = None
        self.__layers = None
        # self.__features = None
        self.__altitudes = None
        self.__extras = None
        self.__adjustments = None
        self.__inSelection = False
        self.__selectedIds = None
        self.__selectedStarts = None
        self.__selectedDirections = None
        self.__startVertex = None
        self.__endVertex = None
        self.ownSettings = None
        self.__usedMnts = None
        self.__isfloating = False
        self.__dockGeom = None

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
        self.__dockWdg = ProfileDockWidget(self.__iface, self.__dockGeom, True)
        if self.__isfloating:
            self.__dockWdg.show()
        else:
            self.__iface.addDockWidget(Qt.BottomDockWidgetArea, self.__dockWdg)
        self.__dockWdg.closeSignal.connect(self.__closed)

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
        if self.__dockWdg is not None:
            self.__dockWdg.close()
        QgsMapTool.deactivate(self)

    def __cancel(self):
        """
        To cancel used variables
        """
        if self.ownSettings.drawdownLayer is not None:
            self.ownSettings.drawdownLayer.removeSelection()
        self.__isChoosed = False
        self.__lastFeatureId = None
        self.__lastFeature = None
        self.__selectedIds = None
        self.__selectedDirections = None
        self.__startVertex = None
        self.__endVertex = None
        self.__inSelection = False
        self.__adjDlg = None
        self.__editDlg = None
        self.__confDlg = None

    def setEnable(self):
        """
        To check if we can enable the action for the selected layer
        """
        enable = True
        if self.ownSettings is None or self.ownSettings.refLayers is None or len(self.ownSettings.refLayers) == 0 \
                or self.ownSettings.levelAtt is None or self.ownSettings.levelVals is None \
                or self.ownSettings.levelVals == [] or self.ownSettings.drawdownLayer is None \
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
        return

    def __updateProfile(self):
        self.__lineVertices()
        for p in range(len(self.__points)):
            pt = self.__points[p]
            x = pt['x']
            y = pt['y']
            z = pt['z']

            for layer in self.__layers:
                laySettings = QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Vertex, self.SEARCH_TOLERANCE,
                                                           QgsTolerance.LayerUnits)
                f_l = Finder.findClosestFeatureAt(self.toMapCoordinates(layer, QgsPoint(x, y)),
                                                  self.canvas(), [laySettings])
                if f_l is None:
                    z.append(None)
                else:
                    if layer == self.ownSettings.drawdownLayer:
                        f_ok = None
                        if f_l[0].id() not in self.__selectedIds:
                            f_ok = f_l[0]
                        else:
                            fs = Finder.findFeaturesAt(QgsPoint(x, y), laySettings, self)
                            for f in fs:
                                if f.id() not in self.__selectedIds:
                                    vertex = f.geometry().closestVertex(QgsPoint(x, y))
                                    if vertex[4] < self.SEARCH_TOLERANCE:
                                        f_ok = f
                                        break
                        if f_ok is not None:
                            closest = f_ok.geometry().closestVertex(QgsPoint(x, y))
                            line, curved = GeometryV2.asLineV2(f_ok.geometry(), self.__iface)
                            zp = line.zAt(closest[1])
                            if zp is None or zp != zp:
                                z.append(0)
                            else:
                                z.append(zp)
                        else:
                            z.append(None)
                    else:
                        zp = GeometryV2.asPointV2(f_l[0].geometry(), self.__iface).z()
                        if zp is None or zp != zp:
                            zp = 0
                        z.append(zp)
        self.__calculateProfile()


    def __adjust(self):
        self.__layers = self.__lineVertices(True)
        self.__adjustments = []
        self.__altitudes = []
        # self.__features = []

        for p in range(len(self.__points)):
            # feat = []
            pt = self.__points[p]
            x = pt['x']
            y = pt['y']
            z = pt['z']
            num_lines = len(self.__selectedIds)
            drawdown = False
            level = None
            for layer in self.ownSettings.refLayers:
                laySettings = QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Vertex, self.SEARCH_TOLERANCE,
                                                           QgsTolerance.LayerUnits)
                f_l = Finder.findClosestFeatureAt(self.toMapCoordinates(layer, QgsPoint(x, y)),
                                                  self.canvas(), [laySettings])
                if f_l is not None:
                    feature = f_l[0]
                    point_v2 = GeometryV2.asPointV2(feature.geometry(), self.__iface)
                    if point_v2.z() > 0:
                        if level is not None:
                            if (level - point_v2.z()) > 0.005:
                                self.__iface.messageBar().pushMessage(
                                    QCoreApplication.translate(
                                        "VDLTools", "More than one reference point, with 2 different elevations !!"),
                                    level=QgsMessageBar.CRITICAL, duration=0)
                                self.__cancel()
                                return
                        level = point_v2.z()
                    comp = QCoreApplication.translate("VDLTools", " (at invert)")
                    adj_ref = False
                    if str(feature.attribute(self.ownSettings.levelAtt)) in self.ownSettings.levelVals:
                        drawdown = True
                        comp = QCoreApplication.translate("VDLTools", " (on pipe)")
                        adj_ref = True

                    self.__adjustments.append({'point': p, 'previous': point_v2.z(), 'line': False, 'adj_ref': adj_ref,
                                               'layer': f_l[1], 'comp': comp, 'feature': f_l[0], 'delta': False})
            diam = 0
            for i in range(num_lines):
                if z[i] is None:
                    continue
                id_s = self.__selectedIds[i]
                feature = QgsFeature()
                self.ownSettings.drawdownLayer.getFeatures(QgsFeatureRequest().setFilterFid(id_s)).nextFeature(feature)
                dtemp = feature.attribute(self.ownSettings.pipeDiam)/1000
                if dtemp > diam:
                    diam = dtemp
                selected = None
                for f in self.ownSettings.drawdownLayer.selectedFeatures():
                    if f.id() == id_s:
                        selected = f
                        break
                self.__adjustments.append({'point': p, 'previous': z[i], 'line': True, 'adj_ref': False,
                                           'layer': self.ownSettings.drawdownLayer, 'feature': selected, 'delta': True})

            for layer in self.__layers:
                laySettings = QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Vertex, self.SEARCH_TOLERANCE,
                                                           QgsTolerance.LayerUnits)
                f_l = Finder.findClosestFeatureAt(self.toMapCoordinates(layer, QgsPoint(x, y)),
                                                  self.canvas(), [laySettings])
                if f_l is None:
                    # feat.append(None)
                    z.append(None)
                else:
                    if layer == self.ownSettings.drawdownLayer:
                        f_ok = None
                        if f_l[0].id() not in self.__selectedIds:
                            f_ok = f_l[0]
                        else:
                            fs = Finder.findFeaturesAt(QgsPoint(x, y), laySettings, self)
                            for f in fs:
                                if f.id() not in self.__selectedIds:
                                    vertex = f.geometry().closestVertex(QgsPoint(x, y))
                                    if vertex[4] < self.SEARCH_TOLERANCE:
                                        f_ok = f
                                        break
                        if f_ok is not None:
                            closest = f_ok.geometry().closestVertex(QgsPoint(x, y))
                            # feat.append(f_ok)
                            line, curved = GeometryV2.asLineV2(f_ok.geometry(), self.__iface)
                            zp = line.zAt(closest[1])

                            dtemp = f_ok.attribute(self.ownSettings.pipeDiam) / 1000
                            if dtemp > diam:
                                diam = dtemp
                            self.__adjustments.append({'point': p, 'previous': zp, 'line': True, 'adj_ref': False,
                                                       'layer': f_l[1], 'comp': " conn.", 'feature': f_ok,
                                                       'delta': True})
                            if zp is None or zp != zp:
                                z.append(0)
                            else:
                                z.append(zp)
                        else:
                            # feat.append(None)
                            z.append(None)
                    else:
                        zp = GeometryV2.asPointV2(f_l[0].geometry(), self.__iface).z()
                        # feat.append(f_l[0])
                        if zp is None or zp != zp:
                            zp = 0
                        z.append(zp)
                        if layer in self.ownSettings.adjLayers:
                            self.__adjustments.append({'point': p, 'previous': zp, 'line': False, 'adj_ref': False,
                                                       'layer': f_l[1], 'feature': f_l[0], 'delta': True})

            # self.__features.append(feat)

            if level is not None:
                if drawdown:
                    alt = level - diam
                else:
                    alt = level
            else:
                alt = None

            dd = None
            if drawdown:
                dd = QCoreApplication.translate("VDLTools", "dradown")
            self.__altitudes.append({'diam': diam, 'drawdown': dd, 'alt': alt})

        last = len(self.__altitudes)-1
        self.__extras = []
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
                        d1 = Finder.sqrDistForCoords(next_pt['x'], pt['x'], next_pt['y'], pt['y'])
                        inter_alt = old_div((d0*next_alt + d1*prev_alt), (d0 + d1))
                        self.__altitudes[i]['alt'] = inter_alt
                        self.__altitudes[i]['drawdown'] = "interpolation"
                elif i == 0 and len(self.__altitudes) > 2:
                    alt1 = self.__altitudes[1]['alt']
                    alt2 = self.__altitudes[2]['alt']
                    if alt1 is not None and alt2 is not None:
                        pt2 = self.__points[2]
                        pt1 = self.__points[1]
                        pt = self.__points[0]
                        big_d = Finder.sqrDistForCoords(pt2['x'], pt1['x'], pt2['y'], pt1['y'])
                        small_d = Finder.sqrDistForCoords(pt1['x'], pt['x'], pt1['y'], pt['y'])
                        alt = alt2 + (1 + old_div(small_d, big_d)) * (alt1 - alt2)
                        if small_d < (old_div(big_d, 4)):
                            self.__altitudes[i]['alt'] = alt
                            self.__altitudes[i]['drawdown'] = "extrapolation"
                        else:
                            self.__extras.append([i, alt])
                elif i == last and len(self.__altitudes) > 2:
                    alt1 = self.__altitudes[i-1]['alt']
                    alt2 = self.__altitudes[i-2]['alt']
                    if alt1 is not None and alt2 is not None:
                        pt2 = self.__points[i-2]
                        pt1 = self.__points[i-1]
                        pt = self.__points[i]
                        big_d = Finder.sqrDistForCoords(pt2['x'], pt1['x'], pt2['y'], pt1['y'])
                        small_d = Finder.sqrDistForCoords(pt1['x'], pt['x'], pt1['y'], pt['y'])
                        alt = alt2 + (1 + old_div(small_d, big_d)) * (alt1 - alt2)
                        if small_d < (old_div(big_d, 4)):
                            self.__altitudes[i]['alt'] = alt
                            self.__altitudes[i]['drawdown'] = "extrapolation"
                        else:
                            self.__extras.append([i, alt])

        if len(self.__extras) == 0:
            self.__setAdjustements()
        else:
            self.__checkForceExtrapolation()

    def __setAdjustements(self):
        self.__calculateProfile()
        self.__adjDlg = DrawdownAdjustmentDialog(self.__adjustments, self.__altitudes)
        self.__adjDlg.rejected.connect(self.__cancel)
        self.__adjDlg.cancelButton().clicked.connect(self.__onAdjCancel)
        self.__adjDlg.applyButton().clicked.connect(self.__onAdjOk)
        self.__adjDlg.show()

    def __checkForceExtrapolation(self):
        message = ""
        for extra in self.__extras:
            message += str(extra[0]) + ") " + \
                       QCoreApplication.translate("VDLTools",
                                                  "The segment is too big, do you really want "
                                                  "to extrapolate anyway ? (elevation : ") + \
                       str(extra[1]) + "m) ? \n"
        self.__confDlg = DrawdownConfirmDialog(message)
        self.__confDlg.okButton().clicked.connect(self.__onConfOk)
        self.__confDlg.cancelButton().clicked.connect(self.__onConfCancel)
        self.__confDlg.show()

    def __onConfOk(self):
        self.__confDlg.accept()
        for extra in self.__extras:
            self.__altitudes[extra[0]]['alt'] = extra[1]
            self.__altitudes[extra[0]]['drawdown'] = "extrapolation"
        self.__setAdjustements()

    def __onConfCancel(self):
        self.__confDlg.reject()
        for extra in self.__extras:
            self.__altitudes[extra[0]]['drawdown'] = QCoreApplication.translate("VDLTools", "cannot be extrapolated")
        self.__setAdjustements()

    def __onAdjOk(self):
        self.__adjDlg.accept()
        layers = []
        for adj in self.__adjDlg.getAdjusts():
            if not adj['layer'].isEditable() and adj['layer'] not in layers:
                layers.append(adj['layer'])
        if len(layers) == 0:
            self.__applyAdjustments()
        else:
            self.__editDlg = DrawdownEditionDialog(layers)
            self.__editDlg.rejected.connect(self.__cancel)
            self.__editDlg.cancelButton().clicked.connect(self.__onEditCancel)
            self.__editDlg.okButton().clicked.connect(self.__onEditOk)
            self.__editDlg.show()

    def __onEditCancel(self):
        self.__editDlg.reject()
        self.__cancel()

    def __onEditOk(self):
        self.__editDlg.accept()
        for layer in self.__editDlg.getLayers():
            layer.startEditing()
        self.__applyAdjustments()


    def __applyAdjustments(self):
        lines = {}
        for adj in self.__adjDlg.getAdjusts():
            if self.__altitudes[adj['point']]['alt'] is None:
                continue
            if adj['line']:
                id_f = adj['feature'].id()
                if id_f not in lines:
                    line_v2, curved = GeometryV2.asLineV2(adj['feature'].geometry(), self.__iface)
                    lines[id_f] = line_v2
                line = lines[id_f]
                i = 0
                for iden in self.__selectedIds:
                    if iden == id_f:
                        break
                    i += 1
                index = adj['point']-self.__selectedStarts[i]
                if not self.__selectedDirections[i]:
                    index = line.numPoints()-1-index
                line.setZAt(index, self.__altitudes[adj['point']]['alt'])
            else:
                pt = adj['point']
                self.__changePoint(adj['layer'], adj['feature'], self.__altitudes[pt]['alt'])
        for key, line in lines.items():
            geom = QgsGeometry(line.clone())
            self.ownSettings.drawdownLayer.changeGeometry(key, geom)
        self.__updateProfile()
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
        layer.changeGeometry(feat.id(), QgsGeometry(feat_v2))

    def __lineVertices(self, checkLayers=False):
        """
        To check if vertices of others layers are crossing the displaying line
        :param checkLayers: if we want to get the list of the other layers in return
        :return: other layers list if requested
        """
        if checkLayers:
            otherLayers = []
        self.__points = []
        self.__selectedStarts = []
        num = 0
        num_lines = len(self.__selectedIds)
        for iden in self.__selectedIds:
            self.__selectedStarts.append(max(0, len(self.__points)-1))
            direction = self.__selectedDirections[num]
            selected = None
            for f in self.ownSettings.drawdownLayer.selectedFeatures():
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
                        combinedLayers = [self.ownSettings.drawdownLayer]
                        combinedLayers += self.ownSettings.refLayers + self.ownSettings.adjLayers
                        for layer in combinedLayers:
                            if layer in otherLayers:
                                continue
                            laySettings = QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Vertex, self.SEARCH_TOLERANCE,
                                                                       QgsTolerance.LayerUnits)
                            f_l = Finder.findClosestFeatureAt(self.toMapCoordinates(layer, QgsPoint(x, y)),
                                                              self.canvas(), [laySettings])

                            if f_l is not None:
                                if layer == self.ownSettings.drawdownLayer:
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

    def __getNames(self):
        """
        To get the names from connected lines layers
        :return: the names list
        """
        names = [self.ownSettings.drawdownLayer.name()]
        for layer in self.__layers:
            if layer.name() == self.ownSettings.drawdownLayer.name():
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
            if self.ownSettings.drawdownLayer is not None:
                laySettings = QgsSnappingUtils.LayerConfig(self.ownSettings.drawdownLayer, QgsPointLocator.All, 10,
                                                           QgsTolerance.Pixels)
                f_l = Finder.findClosestFeatureAt(event.mapPoint(), self.canvas(), [laySettings])
                if not self.__inSelection:
                    if f_l is not None and self.__lastFeatureId != f_l[0].id():
                        self.__lastFeature = f_l[0]
                        self.__lastFeatureId = f_l[0].id()
                        self.ownSettings.drawdownLayer.setSelectedFeatures([f_l[0].id()])
                    if f_l is None:
                        self.__cancel()
                else:
                    if f_l is not None and (self.__selectedIds is None or f_l[0].id() not in self.__selectedIds):
                        line = f_l[0].geometry().asPolyline()
                        if self.__contains(line, self.__endVertex) > -1:
                            self.__lastFeature = f_l[0]
                            self.__lastFeatureId = f_l[0].id()
                            features = self.__selectedIds + [f_l[0].id()]
                            self.ownSettings.drawdownLayer.setSelectedFeatures(features)

                        elif self.__contains(line, self.__startVertex) > -1:
                            self.__lastFeature = f_l[0]
                            self.__lastFeatureId = f_l[0].id()
                            features = self.__selectedIds + [f_l[0].id()]
                            self.ownSettings.drawdownLayer.setSelectedFeatures(features)

                        else:
                            self.ownSettings.drawdownLayer.setSelectedFeatures(self.__selectedIds)
                            self.__lastFeatureId = None
                            self.__lastFeature = None

                if f_l is None:
                    if self.__selectedIds is not None:
                        self.ownSettings.drawdownLayer.setSelectedFeatures(self.__selectedIds)
                    self.__lastFeatureId = None
                    self.__lastFeature = None

    def canvasReleaseEvent(self, event):
        """
        When the mouse is clicked
        :param event: mouse event
        """
        if event.button() == Qt.RightButton:
            if self.ownSettings.drawdownLayer.selectedFeatures() is not None and self.__selectedIds is not None:
                self.__isChoosed = True
                self.__adjust()
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
                    self.ownSettings.drawdownLayer.setSelectedFeatures(self.__selectedIds)

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
