# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-04-13
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
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor
from qgis.core import QgsGeometry, QgsPoint, QgsFeature, QGis
from qgis.core import QgsMapLayer, QgsSnapper, QgsTolerance, QgsFeatureRequest, QgsMapLayerRegistry, QgsVectorLayer
from qgis.gui import QgsMapTool, QgsRubberBand
from math import cos, sin, pi


from intersect_distance_dialog import IntersectDistanceDialog


class IntersectTool(QgsMapTool):
    def __init__(self, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.mapCanvas = iface.mapCanvas()
        self.icon_path = ':/plugins/VDLTools/tools/intersect_icon.png'
        self.text = 'From intersection'
        self.setCursor(Qt.ArrowCursor)
        self.lineLayerID = None
        self.pointLayerID = None

    def setTool(self):
        self.mapCanvas.setMapTool(self)

    def setDistanceDialog(self, mapPoint):
        self.dstDlg = IntersectDistanceDialog(mapPoint)
        self.dstDlg.okButton.clicked.connect(self.dstOk)
        self.dstDlg.cancelButton.clicked.connect(self.dstCancel)
        self.dstDlg.observation.setValue(5.0)
        self.dstDlg.show()

    def dstOk(self):
        self.rubber.reset()
        observation = float(self.dstDlg.observation.text())
        geometry = QgsGeometry().fromPolyline([QgsPoint(self.dstDlg.mapPoint.x() + observation * cos(pi / 180 * a),
                                                        self.dstDlg.mapPoint.y() + observation * sin(pi / 180 * a))
                                    for a in range(0, 361, 3)])
        lineLayer = self.lineLayer()
        lineLayer.startEditing()
        feature = QgsFeature()
        feature.setGeometry(geometry)
        lineLayer.addFeature(feature)
        lineLayer.updateExtents()
        lineLayer.commitChanges()

        # center
        pointLayer = self.pointLayer()
        pointLayer.startEditing()
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry().fromPoint(self.dstDlg.mapPoint))
        pointLayer.addFeature(feature)
        pointLayer.updateExtents()
        pointLayer.commitChanges()

        self.dstDlg.close()


    def dstCancel(self):
        self.dstDlg.close()
        self.rubber.reset()

    def activate(self):
        QgsMapTool.activate(self)
        self.rubber = QgsRubberBand(self.mapCanvas, QGis.Point)
        color = QColor("red")
        color.setAlphaF(0.78)
        self.rubber.setColor(color)
        self.rubber.setIcon(4)
        self.rubber.setIconSize(12)
        self.updateSnapperList()
        self.mapCanvas.layersChanged.connect(self.updateSnapperList)
        self.mapCanvas.scaleChanged.connect(self.updateSnapperList)
        self.messageWidget = self.iface.messageBar().createMessage("Intersect Tool", "Not snapped.")
        self.messageWidgetExist = True
        self.messageWidget.destroyed.connect(self.messageWidgetRemoved)
        self.iface.messageBar().pushWidget(self.messageWidget)

    def updateSnapperList(self):
        self.snapperList = []
        scale = self.iface.mapCanvas().mapRenderer().scale()
        for layer in self.iface.mapCanvas().layers():
            if layer.type() == QgsMapLayer.VectorLayer and layer.hasGeometryType():
                if not layer.hasScaleBasedVisibility() or layer.minimumScale() < scale <= layer.maximumScale():
                    snapLayer = QgsSnapper.SnapLayer()
                    snapLayer.mLayer = layer
                    snapLayer.mSnapTo = QgsSnapper.SnapToVertex
                    snapLayer.mTolerance = 7
                    snapLayer.mUnitType = QgsTolerance.Pixels
                    self.snapperList.append(snapLayer)

    def deactivate(self):
        self.iface.messageBar().popWidget(self.messageWidget)
        self.rubber.reset()
        self.mapCanvas.layersChanged.disconnect(self.updateSnapperList)
        self.mapCanvas.scaleChanged.disconnect(self.updateSnapperList)
        QgsMapTool.deactivate(self)

    def messageWidgetRemoved(self):
        self.messageWidgetExist = False

    def displaySnapInfo(self, snappingResults):
        if not self.messageWidgetExist:
            return
        nSnappingResults = len(snappingResults)
        if nSnappingResults == 0:
            message = "No snap"
        else:
            message = "Snapped to: <b>%s" % snappingResults[0].layer.name() + "</b>"
            if nSnappingResults > 1:
                layers = []
                message += " Nearby: "
                for res in snappingResults[1:]:
                    layerName = res.layer.name()
                    if layerName not in layers:
                        message += res.layer.name() + ", "
                        layers.append(layerName)
                message = message[:-2]
        if self.messageWidgetExist:
            self.messageWidget.setText(message)

    def canvasMoveEvent(self, mouseEvent):
        self.rubber.reset()
        snappedFeature = self.snapToIntersection(mouseEvent.pos())
        if snappedFeature is None:
            snappedPoint = self.snapToLayers(mouseEvent.pos())
            if snappedPoint is not None:
                self.rubber.setToGeometry(QgsGeometry().fromPoint(snappedPoint), None)
        else:
            self.rubber.addGeometry(snappedFeature.geometry(), None)


    def canvasPressEvent(self, mouseEvent):
        if mouseEvent.button() != Qt.LeftButton:
            return
        pixPoint = mouseEvent.pos()
        mapPoint = self.toMapCoordinates(pixPoint)
        #snap to layers
        snappedFeature = self.snapToIntersection(mouseEvent.pos())
        if snappedFeature is None:
            snappedPoint = self.snapToLayers(mouseEvent.pos())
            if snappedPoint is not None:
                self.rubber.setToGeometry(QgsGeometry().fromPoint(snappedPoint), None)
                mapPoint = snappedPoint
        else:
            self.rubber.addGeometry(snappedFeature.geometry(), None)
            mapPoint = snappedFeature.geometry()
        self.setDistanceDialog(mapPoint)

    def snapToIntersection(self, pixPoint):
        # do the snapping
        snapper = QgsSnapper(self.mapCanvas.mapRenderer())
        snapper.setSnapLayers(self.snapperList)
        snapper.setSnapMode(QgsSnapper.SnapWithResultsWithinTolerances)
        ok, snappingResults = snapper.snapPoint(pixPoint, [])
        # output snapped features
        features = []
        alreadyGot = []
        for result in snappingResults:
            featureId = result.snappedAtGeometry
            f = QgsFeature()
            if (result.layer.id(), featureId) not in alreadyGot:
                if result.layer.getFeatures(QgsFeatureRequest().setFilterFid(featureId)).nextFeature(f) is False:
                    continue
                if not isFeatureRendered(self.mapCanvas, result.layer, f):
                    continue
                features.append(QgsFeature(f))
                features[-1].layer = result.layer
                alreadyGot.append((result.layer.id(), featureId))
        return features


    def snapToLayers(self, pixPoint):
        if len(self.snapperList) == 0:
            return None
        snapper = QgsSnapper(self.mapCanvas.mapRenderer())
        snapper.setSnapLayers(self.snapperList)
        snapper.setSnapMode(QgsSnapper.SnapWithResultsWithinTolerances)
        ok, snappingResults = snapper.snapPoint(pixPoint, [])
        self.displaySnapInfo(snappingResults)
        if ok == 0 and len(snappingResults) > 0:
            return QgsPoint(snappingResults[0].snappedVertex)
        else:
            return None

    def lineLayer(self):
        layer = QgsMapLayerRegistry.instance().mapLayer(self.lineLayerID)
        if layer is None:
            epsg = self.iface.mapCanvas().mapRenderer().destinationCrs().authid()
            layer = QgsVectorLayer("LineString?crs=%s&index=yes" % epsg, "Memory Lines", "memory")
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            layer.layerDeleted.connect(self.__lineLayerDeleted)
            self.lineLayerID = layer.id()
        else:
            self.iface.legendInterface().setLayerVisible(layer, True)
        return layer

    def __lineLayerDeleted(self):
        self.lineLayerID = None

    def pointLayer(self):
        layer = QgsMapLayerRegistry.instance().mapLayer(self.pointLayerID)
        if layer is None:
            epsg = self.iface.mapCanvas().mapRenderer().destinationCrs().authid()
            layer = QgsVectorLayer("Point?crs=%s&index=yes" % epsg, "Memory Points", "memory")
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            layer.layerDeleted.connect(self.__pointLayerDeleted)
            self.pointLayerID = layer.id()
        else:
            self.iface.legendInterface().setLayerVisible(layer, True)
        return layer

    def __pointLayerDeleted(self):
        self.pointLayerID = None
