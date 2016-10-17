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

from PyQt4.QtCore import QPoint
from qgis.core import (QgsPoint,
                       QgsVectorLayer,
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


class Finder:
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
        :return: features found in layers
        """
        match = Finder.snap(mapPoint, mapCanvas, layersConfigs, QgsSnappingUtils.SnapAdvanced)
        if match.featureId():
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
    def findFeaturesLayersAt(mapPoint, layersConfig, mapTool):
        """
        To find features from a given position in given layers
        :param mapPoint: the map position
        :param layersConfig: the layers in which we are looking for features
        :param mapTool: a QgsMapTool instance
        :return: features found in layers
        """
        features = []
        for layerConfig in layersConfig:
            features += Finder.findFeaturesAt(mapPoint, layerConfig, mapTool)
        return features

    @staticmethod
    def findFeaturesAt(mapPoint, layerConfig, mapTool):
        """
        To find features from a given position in a given layer
        :param mapPoint: the map position
        :param layerConfig: the layer in which we are looking for features
        :param mapTool: a QgsMapTool instance
        :return: features found in layer
        """
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
    def intersect(geometry1, geometry2, mousePoint):
        """
        To check if there is an intersection between 2 geometries close to a given point
        :param geometry1: the first geometry
        :param geometry2: the second geometry
        :param mousePoint: the given point
        :return: the intersection as QgsPoint or none
        """
        intersection = geometry1.intersection(geometry2)
        intersectionMP = intersection.asMultiPoint()
        intersectionP = intersection.asPoint()
        if len(intersectionMP) == 0:
            intersectionMP = intersection.asPolyline()
        if len(intersectionMP) == 0 and intersectionP == QgsPoint(0, 0):
            return None
        if len(intersectionMP) > 1:
            intersectionP = intersectionMP[0]
            for point in intersectionMP[1:]:
                if mousePoint.sqrDist(point) < mousePoint.sqrDist(intersectionP):
                    intersectionP = QgsPoint(point.x(), point.y())
        if intersectionP != QgsPoint(0, 0):
            return intersectionP
        else:
            return None

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
        snap_layers = []
        for layer in mapCanvas.layers():
            types = [0, 1, 2]
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() in types:
                noUse, enabled, snappingType, unitType, tolerance, avoidIntersection = \
                    QgsProject.instance().snapSettingsForLayer(layer.id())
                if isinstance(layer, QgsVectorLayer) and enabled:
                    if snappingType == QgsSnapper.SnapToVertex:
                        snap_type = QgsPointLocator.Vertex
                    elif snappingType == QgsSnapper.SnapToSegment:
                        snap_type = QgsPointLocator.Edge
                    else:
                        snap_type = QgsPointLocator.All
                    snap_layers.append(QgsSnappingUtils.LayerConfig(layer, snap_type, tolerance, unitType))

        features = Finder.findFeaturesLayersAt(mapPoint, snap_layers, mapTool)
        if len(features) > 1:
            if len(features) > 2:
                one = [-1, 9999999]
                two = [-1, 9999999]
                for i in xrange(len(features)):
                    d = Finder.sqrDistForPoints(mapPoint, features[i].geometry().asPoint())
                    if d > one[1]:
                        two = one
                        one[0] = i
                        one[1] = d
                    elif d > two[1]:
                        two[0] = i
                        two[1] = d
                feat1 = features[one[0]]
                feat2 = features[two[0]]
            else:
                feat1 = features[0]
                feat2 = features[1]
            if not featureId or feat1.id() == featureId or feat2.id() == featureId:
                return Finder.intersect(feat1.geometry(), feat2.geometry(), mapPoint)
            else:
                return None
        else:
            return None

    @staticmethod
    def snap(mapPoint, mapCanvas, layersConfigs=None, mode=None):
        """
        To snap on given layers for a given point
        :param mapPoint: the map position
        :param mapCanvas: the used QgsMapCanvas
        :param layersConfig: the layers in which we are looking for features
        :param mode: snapping mode
        :return: snapping match instance
        """
        snap_util = mapCanvas.snappingUtils()
        if layersConfigs:
            old_layers = snap_util.layers()
            old_mode = snap_util.snapToMapMode()
            snap_util.setLayers(layersConfigs)
            if mode:
                snap_util.setSnapToMapMode(mode)
            match = snap_util.snapToMap(mapPoint)
            snap_util.setLayers(old_layers)
            snap_util.setSnapToMapMode(old_mode)
        else:
            match = snap_util.snapToMap(mapPoint)
        return match
