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
from qgis.core import (QGis,
                       QgsMapLayer)
from qgis.gui import (QgsMapTool,
                      QgsMessageBar)
from PyQt4.QtCore import Qt
from ..core.finder import Finder
from ..ui.profile_layers_dialog import ProfileLayersDialog
from ..ui.profile_dock_widget import ProfileDockWidget

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
        self.__wkbLine = QGis.WKBLineString
        self.__wkbPoint = QGis.WKBPoint
        self.setCursor(Qt.ArrowCursor)
        self.__isChoosed = False
        self.__lastFeatureId = None
        self.__selectedFeature = None
        self.__dockWdg = None

    def icon_path(self):
        return self.__icon_path

    def text(self):
        return self.__text

    def setTool(self):
        self.__oldTool = self.__canvas.mapTool()
        self.__canvas.setMapTool(self)

    def setEnable(self, layer):
        self.__setLayer(layer)

    def activate(self):
        QgsMapTool.activate(self)
        self.__dockWdg = ProfileDockWidget(self.__iface)
        self.__iface.addDockWidget(Qt.BottomDockWidgetArea, self.__dockWdg)

    def deactivate(self):
        if self.__dockWdg is not None:
            self.__dockWdg.close()
        if QgsMapTool is not None:
            QgsMapTool.deactivate(self)

    def __setLayer(self, layer):
        if layer is not None\
                and layer.type() == self.__vectorKind and layer.wkbType() == self.__wkbLine:
            self.__lineLayer = layer
            self.action().setEnabled(True)
            return
        self.action().setEnabled(False)
        self.__lineLayer = None

    def __setLayerDialog(self, pointLayers):
        self.__layDlg = ProfileLayersDialog(pointLayers)
        self.__layDlg.okButton().clicked.connect(self.__layOk)
        self.__layDlg.cancelButton().clicked.connect(self.__layCancel)

    def __getPointLayers(self):
        layerList = []
        for layer in self.__iface.mapCanvas().layers():
            if layer.type() == self.__vectorKind and layer.hasGeometryType() and layer.wkbType() == self.__wkbPoint:
                    layerList.append(layer)
        return layerList

    def __layCancel(self):
        self.__layDlg.close()
        self.__isChoosed = 0
        self.__lineLayer.removeSelection()

    def __layOk(self):
        self.__layDlg.close()
        layers, attributes = self.__layDlg.getLayersAndAttributes()
        line = self.__selectedFeature.geometry().asPolyline()
        pointz = {}
        for i in xrange(len(line)):
            vertex = self.toCanvasCoordinates(line[i])
            pointz[i] = Finder.findClosestFeatureLayersAt(vertex, layers, self)
        points = []
        for key, p in pointz.items():
            if p is not None:
                pt = p[0].geometry().asPoint()
                i = 0
                for l in layers:
                    if l == p[1]:
                        break
                    i += 1
                attName = attributes[i]
                z = p[0].attribute(attName)
                points.append({'x': pt.x(), 'y': pt.y(), 'z': z})
        self.__calculateProfil(points)

        self.__isChoosed = 0
        self.__lineLayer.removeSelection()

    def canvasMoveEvent(self, event):
        if not self.__isChoosed:
            if Finder is not None:
                f = Finder.findClosestFeatureAt(event.pos(), self.__lineLayer, self)
                if f and self.__lastFeatureId != f.id():
                    self.__lastFeatureId = f.id()
                    self.__lineLayer.setSelectedFeatures([f.id()])
                if not f:
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

    def __calculateProfil(self, points, vertline = True):
        if points is None:
            return
        self.__dockWdg.clearData()
        if len(points) == 0:
            return
        self.__dockWdg.setProfiles(points)
        if vertline:						#Plotting vertical lines at the node of polyline draw
            self.__dockWdg.drawVertLine()

        self.__dockWdg.attachCurves()
