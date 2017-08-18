# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-05-03
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
from future.builtins import range
from future.builtins import object

from PyQt4.QtCore import QPoint
from qgis.core import (QgsPoint,QgsGeometry,
                       QGis,
                       QgsMapLayer,
                       QgsTolerance,
                       QgsPointLocator,
                       QgsProject,
                       QgsSnapper,
                       QgsSnappingUtils,
                       QgsRectangle,
                       QgsFeatureRequest,
                       QgsFeature)
from math import (sqrt,
                  pow)


class Finder(object):
    """
    Class for snapping methods
    """

    @staticmethod
    def findClosestFeatureAt(mapPoint, mapCanvas, layersConfigs=None):
        """
        To find closest feature from a given position in given layers
        :param mapPoint: the map position
        :param mapCanvas: the used QgsMapCanvas
        :param layersConfig: the layers in which we are looking for features
        :return: feature found in layers
        """
        match = Finder.snap(mapPoint, mapCanvas, layersConfigs, QgsSnappingUtils.SnapAdvanced)
        if match.featureId() and match.layer():
            feature = QgsFeature()
            match.layer().getFeatures(QgsFeatureRequest().setFilterFid(match.featureId())).nextFeature(feature)
            return [feature, match.layer()]
        else:
            return None

    @staticmethod
    def sqrDistForPoints(pt1, pt2):
        """
        To calculate the distance between 2 points
        :param pt1: first Point
        :param pt2: second Point
        :return: distance
        """
        return Finder.sqrDistForCoords(pt1.x(), pt2.x(), pt1.y(), pt2.y())

    @staticmethod
    def sqrDistForCoords(x1, x2, y1, y2):
        """
        To calculate the distance between 2 points
        :param x1: X coordinate for the first point
        :param x2: X coordinate for the second point
        :param y1: Y coordinate for the first point
        :param y2: Y coordinate for the second point
        :return: distance
        """
        return sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))

    @staticmethod
    def findFeaturesLayersAt(mapPoint, layersConfig, mapTool, pixTol):
        """
        To find features from a given position in given layers
        :param mapPoint: the map position
        :param layersConfig: the layers in which we are looking for features
        :param mapTool: a QgsMapTool instance
        :param pixTol: tolerance in pixels
        :return: features found in layers
        """
        features = []
        for layerConfig in layersConfig:
            features += Finder.findFeaturesAt(mapPoint, layerConfig, mapTool, pixTol)
        return features

    @staticmethod
    def findFeaturesAt(mapPoint, layerConfig, mapTool, layTolerance=None):
        """
        To find features from a given position in a given layer
        :param mapPoint: the map position
        :param layerConfig: the layer in which we are looking for features
        :param mapTool: a QgsMapTool instance
        :param layTolerance: tolerance in layer units
        :return: features found in layer
        """
        if layTolerance is None:
            if layerConfig is None:
                return None
            tolerance = layerConfig.tolerance
            if layerConfig.unit == QgsTolerance.Pixels:
                layTolerance = Finder.calcCanvasTolerance(mapTool.toCanvasCoordinates(mapPoint), layerConfig.layer, mapTool,
                                                          tolerance)
            elif layerConfig.unit == QgsTolerance.ProjectUnits:
                layTolerance = Finder.calcMapTolerance(mapPoint, layerConfig.layer, mapTool, tolerance)
            else:
                layTolerance = tolerance
        layPoint = mapTool.toLayerCoordinates(layerConfig.layer, mapPoint)
        searchRect = QgsRectangle(layPoint.x() - layTolerance, layPoint.y() - layTolerance,
                                  layPoint.x() + layTolerance, layPoint.y() + layTolerance)
        request = QgsFeatureRequest()
        request.setFilterRect(searchRect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)
        features = []
        for feature in layerConfig.layer.getFeatures(request):
            if layerConfig.layer.geometryType() == QGis.Polygon:
                dist, nearest, vertex = feature.geometry().closestSegmentWithContext(mapPoint)
                if QgsGeometry.fromPoint(nearest).intersects(searchRect):
                    features.append(QgsFeature(feature))
            else:
                features.append(QgsFeature(feature))
        return features

    @staticmethod
    def calcCanvasTolerance(pixPoint, layer, mapTool, distance):
        """
        To transform the tolerance from screen coordinates to layer coordinates
        :param pixPoint: a screen position
        :param layer: the layer in which we are working
        :param mapTool: a QgsMapTool instance
        :param distance: the tolerance in map coordinates
        :return: the tolerance in layer coordinates
        """
        pt1 = QPoint(pixPoint.x(), pixPoint.y())
        pt2 = QPoint(pixPoint.x() + distance, pixPoint.y())
        layerPt1 = mapTool.toLayerCoordinates(layer, pt1)
        layerPt2 = mapTool.toLayerCoordinates(layer, pt2)
        tolerance = layerPt2.x() - layerPt1.x()
        return tolerance

    @staticmethod
    def calcMapTolerance(mapPoint, layer, mapTool, distance):
        """
        To transform the tolerance from map coordinates to layer coordinates
        :param mapPoint: a map position
        :param layer: the layer in which we are working
        :param mapTool: a QgsMapTool instance
        :param distance: the tolerance in map coordinates
        :return: the tolerance in layer coordinates
        """
        pt1 = QgsPoint(mapPoint.x(), mapPoint.y())
        pt2 = QgsPoint(mapPoint.x() + distance, mapPoint.y())
        layerPt1 = mapTool.toLayerCoordinates(layer, pt1)
        layerPt2 = mapTool.toLayerCoordinates(layer, pt2)
        tolerance = layerPt2.x() - layerPt1.x()
        return tolerance

    @staticmethod
    def intersect(featureId, feature1, feature2, mousePoint):
        """
        To check if there is an intersection between 2 features close to a given point
        :param featureId: if we want to snap on a given feature
        :param feature1: the first feature
        :param feature2: the second feature
        :param mousePoint: the given point
        :return: the intersection as QgsPoint or none
        """

        if featureId is None or feature1.id() == featureId or feature2.id() == featureId:
            geometry1 = feature1.geometry()
            geometry2 = feature2.geometry()
            if geometry1.type() == 2:
                polygon = geometry1.geometry()
                newG = polygon.boundary()
                geometry1 = QgsGeometry(newG)
            if geometry2.type() == 2:
                polygon = geometry2.geometry()
                newG = polygon.boundary()
                geometry2 = QgsGeometry(newG)

            intersection = geometry1.intersection(geometry2)
            if intersection.type() == 0:
                intersectionP = intersection.asPoint()
                intersectionMP = intersection.asMultiPoint()
                if intersectionMP is not None and len(intersectionMP) > 0:
                    for point in intersectionMP:
                        if intersectionP is None:
                            intersectionP = point
                        elif mousePoint.sqrDist(point) < mousePoint.sqrDist(intersectionP):
                            intersectionP = QgsPoint(point.x(), point.y())
            elif intersection.type() == 1:
                intersectionPL = intersection.asPolyline()
                intersectionMPL = intersection.asMultiPolyline()
                intersectionP = None
                if intersectionMPL is not None and len(intersectionMPL) > 0:
                    for line in intersectionMPL:
                        for point in line:
                            if intersectionP is None:
                                intersectionP = point
                            elif mousePoint.sqrDist(point) < mousePoint.sqrDist(intersectionP):
                                intersectionP = QgsPoint(point.x(), point.y())
                else:
                    for point in intersectionPL:
                        if intersectionP is None:
                            intersectionP = point
                        elif mousePoint.sqrDist(point) < mousePoint.sqrDist(intersectionP):
                            intersectionP = QgsPoint(point.x(), point.y())
            elif intersection.type() == 2:
                intersectionMPL = intersection.asMultiPolyline()
                intersectionP = None
                for line in intersectionMPL:
                    for point in line:
                        if intersectionP is None:
                            intersectionP = point
                        elif mousePoint.sqrDist(point) < mousePoint.sqrDist(intersectionP):
                            intersectionP = QgsPoint(point.x(), point.y())
            else:
                return None

            if intersectionP and intersectionP != QgsPoint(0, 0):
                return intersectionP

        return None

    @staticmethod
    def getLayersSettings(mapCanvas, types, snapType=None):
        """
        To get the snapping config from different layers
        :param mapCanvas: the used QgsMapCanvas
        :param types: geometry types in use
        :param snapType: snapping type
        :return: list of layers config
        """
        snap_layers = []
        for layer in mapCanvas.layers():
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() in types:
                snap_util = mapCanvas.snappingUtils()
                mode = snap_util.snapToMapMode()
                if mode == QgsSnappingUtils.SnapCurrentLayer and layer.id() != mapCanvas.currentLayer().id():
                    continue
                if mode == QgsSnappingUtils.SnapAllLayers:
                    snap_index, tolerance, unitType = snap_util.defaultSettings()
                    snap_type = QgsPointLocator.Type(snap_index)
                else:
                    noUse, enabled, snappingType, unitType, tolerance, avoidIntersection = \
                        QgsProject.instance().snapSettingsForLayer(layer.id())
                    if layer.type() == QgsMapLayer.VectorLayer and enabled:
                        if snapType is None:
                            if snappingType == QgsSnapper.SnapToVertex:
                                snap_type = QgsPointLocator.Vertex
                            elif snappingType == QgsSnapper.SnapToSegment:
                                snap_type = QgsPointLocator.Edge
                            elif snappingType == QgsSnapper.SnapToVertexAndSegment:
                                snap_type = QgsPointLocator.Edge and QgsPointLocator.Vertex
                            else:
                                snap_type = QgsPointLocator.All
                        else:
                            snap_type = snapType
                    else:
                        continue
                snap_layers.append(QgsSnappingUtils.LayerConfig(layer, snap_type, tolerance, unitType))
        return snap_layers

    @staticmethod
    def snapCurvedIntersections(mapPoint, mapCanvas, mapTool, featureId=None):
        """
        To snap on curved intersections
        :param mapPoint: the map position
        :param mapCanvas: the used QgsMapCanvas
        :param mapTool: a QgsMapTool instance
        :param featureId: if we want to snap on a given feature
        :return: intersection point
        """
        layerTolerance = 1
        snap_layers = Finder.getLayersSettings(mapCanvas, [QGis.Line, QGis.Polygon])
        features = Finder.findFeaturesLayersAt(mapPoint, snap_layers, mapTool, layerTolerance)
        inter = None
        if len(features) > 1:
            if len(features) > 2:
                for i in range(len(features)):
                    for j in range(i, len(features)):
                        feat1 = features[i]
                        feat2 = features[j]
                        if feat1 != feat2:
                            interP = Finder.intersect(featureId, feat1, feat2, mapPoint)
                            if interP is not None:
                                if inter is None or mapPoint.sqrDist(interP) < mapPoint.sqrDist(inter):
                                    inter = interP
            else:
                feat1 = features[0]
                feat2 = features[1]
                inter = Finder.intersect(featureId, feat1, feat2, mapPoint)
        return inter

    @staticmethod
    def snap(mapPoint, mapCanvas, layersConfigs=None, mode=None):
        """
        To snap on given layers for a given point
        :param mapPoint: the map position
        :param mapCanvas: the used QgsMapCanvas
        :param layersConfigs: the layers in which we are looking for features
        :param mode: snapping mode
        :return: snapping match instance
        """
        snap_util = mapCanvas.snappingUtils()
        if layersConfigs is not None:
            old_layers = snap_util.layers()
            old_mode = snap_util.snapToMapMode()
            snap_util.setLayers(layersConfigs)
            if mode is not None:
                snap_util.setSnapToMapMode(mode)
            match = snap_util.snapToMap(mapPoint)
            snap_util.setLayers(old_layers)
            snap_util.setSnapToMapMode(old_mode)
        else:
            match = snap_util.snapToMap(mapPoint)
        return match
