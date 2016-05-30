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
                       QGis,
                       QgsPoint,
                       QgsWKBTypes)
from qgis.gui import (QgsMapTool,
                      QgsMessageBar)
from PyQt4.QtCore import Qt
from ..core.finder import Finder
from ..core.geometry_v2 import GeometryV2
from ..ui.profile_layers_dialog import ProfileLayersDialog
from ..ui.profile_dock_widget import ProfileDockWidget
from ..ui.profile_message_dialog import ProfileMessageDialog


class ProfileTool(QgsMapTool):

    def __init__(self, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.__canvas = iface.mapCanvas()
        self.__icon_path = ':/plugins/VDLTools/icons/profile_icon.png'
        self.__text = 'Profile of a line'
        self.__oldTool = None
        self.__lineLayer = None
        self.__vectorKind = QgsMapLayer.VectorLayer
        self.setCursor(Qt.ArrowCursor)
        self.__isChoosed = False
        self.__lastFeatureId = None
        self.__selectedFeature = None
        self.__dockWdg = None
        self.__layDlg = None
        self.__msgDlg = None
        self.__points = None
        self.__layers = None

    def icon_path(self):
        return self.__icon_path

    def text(self):
        return self.__text

    def setTool(self):
        self.__oldTool = self.__canvas.mapTool()
        self.__canvas.setMapTool(self)

    def activate(self):
        QgsMapTool.activate(self)
        self.__dockWdg = ProfileDockWidget(self.__iface)
        self.__iface.addDockWidget(Qt.BottomDockWidgetArea, self.__dockWdg)

    def deactivate(self):
        if self.__dockWdg is not None:
            self.__dockWdg.close()
        if QgsMapTool is not None:
            QgsMapTool.deactivate(self)

    def setEnable(self, layer):
        if layer is not None and layer.type() == self.__vectorKind and \
                        QGis.fromOldWkbType(layer.wkbType()) == QgsWKBTypes.LineStringZ:
            self.__lineLayer = layer
            self.action().setEnabled(True)
            return
        self.action().setEnabled(False)
        if self.__dockWdg is not None:
            self.__dockWdg.close()
        self.__lineLayer = None

    def __setLayerDialog(self, pointLayers):
        self.__layDlg = ProfileLayersDialog(pointLayers)
        self.__layDlg.okButton().clicked.connect(self.__layOk)
        self.__layDlg.cancelButton().clicked.connect(self.__layCancel)

    def __setMessageDialog(self, situations, names):
        self.__msgDlg = ProfileMessageDialog(situations, names, self.__points)
        self.__msgDlg.passButton().clicked.connect(self.__msgPass)
        self.__msgDlg.onLineButton().clicked.connect(self.__onLine)
        self.__msgDlg.onPointsButton().clicked.connect(self.__onPoints)

    def __getPointLayers(self):
        layerList = []
        for layer in self.__iface.mapCanvas().layers():
            if layer.type() == self.__vectorKind and QGis.fromOldWkbType(layer.wkbType()) == QgsWKBTypes.PointZ:
                    layerList.append(layer)
        return layerList

    def __msgPass(self):
        self.__msgDlg.close()

    def __onLine(self):
        self.__msgDlg.close()
        print(self.__msgDlg.getSituations())

    def __onPoints(self):
        self.__msgDlg.close()
        print(self.__msgDlg.getSituations())

    def __layCancel(self):
        self.__layDlg.close()
        self.__isChoosed = 0
        self.__lineLayer.removeSelection()

    def __layOk(self):
        self.__layDlg.close()
        self.__layers = self.__layDlg.getLayers()
        line_v2 = GeometryV2.asLineStringV2(self.__selectedFeature.geometry())
        self.__points = []
        for i in xrange(line_v2.numPoints()):
            pt_v2 = line_v2.pointN(i)
            x = pt_v2.x()
            y = pt_v2.y()
            z = [pt_v2.z()]
            for layer in self.__layers:
                vertex = self.toCanvasCoordinates(QgsPoint(x, y))
                point = Finder.findClosestFeatureAt(vertex, layer, self)
                if point is None:
                    z.append(None)
                else:
                    point_v2 = GeometryV2.asPointV2(point.geometry())
                    z.append(point_v2.z())
            self.__points.append({'x': x, 'y': y, 'z': z})

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
        self.__lineLayer.removeSelection()

    def canvasMoveEvent(self, event):
        if not self.__isChoosed:
            if Finder is not None and self.__lineLayer is not None:
                f = Finder.findClosestFeatureAt(event.pos(), self.__lineLayer, self)
                if f is not None and self.__lastFeatureId != f.id():
                    self.__lastFeatureId = f.id()
                    self.__lineLayer.setSelectedFeatures([f.id()])
                if f is None:
                    self.__lineLayer.removeSelection()
                    self.__lastFeatureId = None

    def canvasReleaseEvent(self, event):
        found_features = self.__lineLayer.selectedFeatures()
        if len(found_features) > 0:
            if len(found_features) < 1:
                self.__iface.messageBar().pushMessage(u"Une seule feature à la fois", level=QgsMessageBar.INFO)
                return
            self.__selectedFeature = found_features[0]
            self.__isChoosed = 1
            pointLayers = self.__getPointLayers()
            self.__setLayerDialog(pointLayers)
            self.__layDlg.show()

    def __calculateProfile(self, names):
        if self.__points is None:
            return
        self.__dockWdg.clearData()
        if len(self.__points) == 0:
            return
        self.__dockWdg.setProfiles(self.__points)
        self.__dockWdg.drawVertLine()						# Plotting vertical lines at the node of polyline draw
        self.__dockWdg.attachCurves(names)

        situations = []
        for p in xrange(len(self.__points)):
            pt = self.__points[p]
            z0 = pt['z'][0]
            tol = 0.01 * z0
            for i in xrange(1, len(pt['z'])):
                if abs(pt['z'][i]-z0) > tol:
                    situations.append({'point': p, 'layer': i})
                    # msg.append("- point {} in layer '{}' (point: {}m | line vertex: {}m) \n"\
                    #     .format(p, names[i], pt['z'][i], z0))
        if len(situations) > 0:
            self.__setMessageDialog(situations, names)
            self.__msgDlg.show()

