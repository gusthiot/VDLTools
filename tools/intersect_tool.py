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
from math import (cos,
                  sin,
                  pi)
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor
from qgis.core import (QgsGeometry,
                       QgsPoint,
                       QgsFeature,
                       QGis)
from qgis.core import (QgsMapLayer,
                       QgsSnapper,
                       QgsTolerance,
                       QgsMapLayerRegistry,
                       QgsVectorLayer)
from qgis.gui import (QgsMapTool,
                      QgsRubberBand)
from ..ui.intersect_distance_dialog import IntersectDistanceDialog
from ..core.finder import Finder


class IntersectTool(QgsMapTool):
    def __init__(self, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.__mapCanvas = iface.mapCanvas()
        self.__icon_path = ':/plugins/VDLTools/icons/intersect_icon.png'
        self.__text = 'From intersection'
        self.setCursor(Qt.ArrowCursor)
        self.__lineLayerID = None
        self.__pointLayerID = None
        self.__counter = 0

    def icon_path(self):
        return self.__icon_path

    def text(self):
        return self.__text

    def setTool(self):
        self.__mapCanvas.setMapTool(self)

    def __setDistanceDialog(self, mapPoint):
        self.__dstDlg = IntersectDistanceDialog(mapPoint)
        self.__dstDlg.okButton().clicked.connect(self.__dstOk)
        self.__dstDlg.cancelButton().clicked.connect(self.__dstCancel)
        self.__dstDlg.observation().setValue(5.0)
        self.__dstDlg.show()

    def __dstOk(self):
        self.__rubber.reset()
        observation = float(self.__dstDlg.observation().text())
        geometry = QgsGeometry().fromPolyline([QgsPoint(self.__dstDlg.mapPoint().x() + observation * cos(pi / 180 * a),
                                                        self.__dstDlg.mapPoint().y() + observation * sin(pi / 180 * a))
                                               for a in range(0, 361, 3)])
        lineLayer = self.__lineLayer()
        lineLayer.startEditing()
        feature = QgsFeature()
        feature.setGeometry(geometry)
        lineLayer.addFeature(feature)
        lineLayer.updateExtents()
        lineLayer.commitChanges()

        # center
        pointLayer = self.__pointLayer()
        pointLayer.startEditing()
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry().fromPoint(self.__dstDlg.mapPoint()))
        pointLayer.addFeature(feature)
        pointLayer.updateExtents()
        pointLayer.commitChanges()

        self.__dstDlg.close()

    def __dstCancel(self):
        self.__dstDlg.close()
        self.__rubber.reset()

    def activate(self):
        QgsMapTool.activate(self)
        self.__rubber = QgsRubberBand(self.__mapCanvas, QGis.Point)
        color = QColor("red")
        color.setAlphaF(0.78)
        self.__rubber.setColor(color)
        self.__rubber.setIcon(4)
        self.__rubber.setIconSize(12)
        self.__updateSnapperList()
        self.__mapCanvas.layersChanged.connect(self.__updateSnapperList)
        self.__mapCanvas.scaleChanged.connect(self.__updateSnapperList)
        self.__messageWidget = self.__iface.messageBar().createMessage("Intersect Tool", "Not snapped.")
        self.__messageWidgetExist = True
        self.__messageWidget.destroyed.connect(self.__messageWidgetRemoved)
        self.__iface.messageBar().pushWidget(self.__messageWidget)

    def __updateSnapperList(self):
        self.__snapperList = []
        self.__layerList = []
        scale = self.__iface.mapCanvas().mapRenderer().scale()
        for layer in self.__iface.mapCanvas().layers():
            if layer.type() == QgsMapLayer.VectorLayer and layer.hasGeometryType():
                if not layer.hasScaleBasedVisibility() or layer.minimumScale() < scale <= layer.maximumScale():
                    snapLayer = QgsSnapper.SnapLayer()
                    snapLayer.mLayer = layer
                    snapLayer.mSnapTo = QgsSnapper.SnapToVertex
                    snapLayer.mTolerance = 7
                    snapLayer.mUnitType = QgsTolerance.Pixels
                    self.__snapperList.append(snapLayer)
                    self.__layerList.append(layer)

    def deactivate(self):
        self.__iface.messageBar().popWidget(self.__messageWidget)
        self.__rubber.reset()
        self.__mapCanvas.layersChanged.disconnect(self.__updateSnapperList)
        self.__mapCanvas.scaleChanged.disconnect(self.__updateSnapperList)
        QgsMapTool.deactivate(self)

    def __messageWidgetRemoved(self):
        self.__messageWidgetExist = False

    def __displaySnapInfo(self, snappingResults):
        if not self.__messageWidgetExist:
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
        if self.__messageWidgetExist:
            self.__messageWidget.setText(message)

    def canvasMoveEvent(self, mouseEvent):
        if self.__counter > 9:
            self.__rubber.reset()
            snappedIntersection = self.__snapToIntersection(mouseEvent.pos())
            if snappedIntersection is None:
                snappedPoint = self.__snapToLayers(mouseEvent.pos())
                if snappedPoint is not None:
                    self.__rubber.setIcon(4)
                    self.__rubber.setToGeometry(QgsGeometry().fromPoint(snappedPoint), None)
            else:
                self.__rubber.setIcon(1)
                self.__rubber.setToGeometry(QgsGeometry().fromPoint(snappedIntersection), None)
            self.__counter = 0
        else:
            self.__counter += 1

    def canvasPressEvent(self, mouseEvent):
        if mouseEvent.button() != Qt.LeftButton:
            return
        # snap to layers
        snappedIntersection = self.__snapToIntersection(mouseEvent.pos())
        if snappedIntersection is None:
            snappedPoint = self.__snapToLayers(mouseEvent.pos())
            if snappedPoint is not None:
                self.__rubber.setIcon(4)
                self.__rubber.setToGeometry(QgsGeometry().fromPoint(snappedPoint), None)
                mapPoint = snappedPoint
                self.__setDistanceDialog(mapPoint)
        else:
            self.__rubber.setIcon(1)
            self.__rubber.setToGeometry(QgsGeometry().fromPoint(snappedIntersection), None)
            mapPoint = snappedIntersection
            self.__setDistanceDialog(mapPoint)

    def __snapToIntersection(self, pixPoint):
        mousePoint = self.toMapCoordinates(pixPoint)
        features = Finder.findFeaturesLayersAt(pixPoint, self.__layerList, self)
        nFeat = len(features)
        intersections = []
        for i in range(nFeat - 1):
            for j in range(i + 1, nFeat):
                intersection = features[i].geometry().intersection(features[j].geometry())
                intersectionMP = intersection.asMultiPoint()
                intersectionP = intersection.asPoint()
                if len(intersectionMP) == 0:
                    intersectionMP = intersection.asPolyline()
                if len(intersectionMP) == 0 and intersectionP == QgsPoint(0, 0):
                    continue
                if len(intersectionMP) > 1:
                    intersectionP = intersectionMP[0]
                    for point in intersectionMP[1:]:
                        if mousePoint.sqrDist(point) < mousePoint.sqrDist(intersectionP):
                            intersectionP = QgsPoint(point.x(), point.y())
                if intersectionP != QgsPoint(0, 0):
                    intersections.append(intersectionP)
        if len(intersections) == 0:
            return None
        intersectionP = intersections[0]
        for point in intersections[1:]:
            if mousePoint.sqrDist(point) < mousePoint.sqrDist(intersectionP):
                intersectionP = QgsPoint(point.x(), point.y())
        return intersectionP

    def __snapToLayers(self, pixPoint):
        if len(self.__snapperList) == 0:
            return None
        snapper = QgsSnapper(self.__mapCanvas.mapRenderer())
        snapper.setSnapLayers(self.__snapperList)
        snapper.setSnapMode(QgsSnapper.SnapWithResultsWithinTolerances)
        ok, snappingResults = snapper.snapPoint(pixPoint, [])
        self.__displaySnapInfo(snappingResults)
        if ok == 0 and len(snappingResults) > 0:
            return QgsPoint(snappingResults[0].snappedVertex)
        else:
            return None

    def __lineLayer(self):
        layer = QgsMapLayerRegistry.instance().mapLayer(self.__lineLayerID)
        if layer is None:
            epsg = self.__iface.mapCanvas().mapRenderer().destinationCrs().authid()
            layer = QgsVectorLayer("LineString?crs=%s&index=yes" % epsg, "Memory Lines", "memory")
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            layer.layerDeleted.connect(self.__lineLayerDeleted)
            self.__lineLayerID = layer.id()
        else:
            self.__iface.legendInterface().setLayerVisible(layer, True)
        return layer

    def __lineLayerDeleted(self):
        self.lineLayerID = None

    def __pointLayer(self):
        layer = QgsMapLayerRegistry.instance().mapLayer(self.__pointLayerID)
        if layer is None:
            epsg = self.__iface.mapCanvas().mapRenderer().destinationCrs().authid()
            layer = QgsVectorLayer("Point?crs=%s&index=yes" % epsg, "Memory Points", "memory")
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            layer.layerDeleted.connect(self.__pointLayerDeleted)
            self.__pointLayerID = layer.id()
        else:
            self.__iface.legendInterface().setLayerVisible(layer, True)
        return layer

    def __pointLayerDeleted(self):
        self.__pointLayerID = None
