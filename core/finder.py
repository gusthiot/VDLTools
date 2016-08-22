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
                       QGis,
                       QgsSnapper,
                       QgsGeometry,
                       QgsRectangle,
                       QgsFeatureRequest,
                       QgsFeature)
from math import (sqrt,
                  pow)


class Finder:

    @staticmethod
    def findClosestFeatureAt(point, layer, mapTool, tolerance=15):
        """
        To find the closest feature from a given position in a given layer
        :param point: the position
        :param layer: the layer in which we are looking for features
        :param mapTool: a QgsMapTool instance
        :param tolerance: the tolerance for finding in point coordinates
        :return: closest feature found or none
        """
        features = Finder.findFeaturesAt(point, layer, mapTool, tolerance)
        if features is not None and len(features) > 0:
            return features[0]
        else:
            return None

    @staticmethod
    def findClosestFeatureLayersAt(point, layers, mapTool, tolerance=15):
        """
        To find the closest feature from a given position in given layers
        :param point: the position
        :param layers: the layers in which we are looking for features
        :param mapTool: a QsMapTool instance
        :param tolerance: the tolerance for finding in point coordinates
        :return: closest feature found or none
        """
        features = []
        for layer in layers:
            feats = Finder.findFeaturesAt(point, layer, mapTool, tolerance)
            if feats is not None:
                for f in feats:
                    features.append([f, layer])
        if len(features) > 0:
            if isinstance(point, QPoint):
                dst = Finder.sqrDistForPoints(point, mapTool.toCanvasCoordinates(features[0][0].geometry().asPoint()))
            else:
                dst = Finder.sqrDistForPoints(point, features[0][0].geometry().asPoint())
            f = 0
            for i in xrange(1,len(features)):
                if isinstance(point, QPoint):
                    d = Finder.sqrDistForPoints(point, mapTool.toCanvasCoordinates(features[i][0].geometry().asPoint()))
                else:
                    dst = Finder.sqrDistForPoints(point, features[i][0].geometry().asPoint())
                if d < dst:
                    dst = d
                    f = i
            return features[f]
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
    def findFeaturesLayersAt(point, layers, mapTool, tolerance=10):
        """
        To find features from a given position in given layers
        :param point: the position
        :param layers: the layers in which we are looking for features
        :param mapTool: a QgsMapTool instance
        :param tolerance: the tolerance for finding in point coordinates
        :return: features found in layers
        """
        features = []
        for layer in layers:
            features += Finder.findFeaturesAt(point, layer, mapTool, tolerance)
        return features

    @staticmethod
    def findFeaturesAt(point, layer, mapTool, tolerance):
        """
        To find features from a given position in a given layer
        :param point: the  position
        :param layer: the layer in which we are looking for features
        :param mapTool: a QgsMapTool instance
        :param tolerance: the tolerance for finding in point coordinates
        :return: features found in layer
        """
        if layer is None:
            return None
        if isinstance(point, QPoint):
            layPoint = mapTool.toLayerCoordinates(layer, point)
            layTolerance = Finder.calcTolerance(point, layer, mapTool, tolerance)
        else:
            layPoint = point
            layTolerance = tolerance
        searchRect = QgsRectangle(layPoint.x() - layTolerance, layPoint.y() - layTolerance,
                                  layPoint.x() + layTolerance, layPoint.y() + layTolerance)
        request = QgsFeatureRequest()
        request.setFilterRect(searchRect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)
        features = []
        for feature in layer.getFeatures(request):
            features.append(QgsFeature(feature))
        return features

    @staticmethod
    def calcTolerance(pixPoint, layer, mapTool, distance):
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
    def snapToIntersection(pixPoint, mapTool, layers):
        """
        To find the closest intersection in different layers for a given point
        :param pixPoint: the screen position
        :param mapTool: a QgsMapTool instance
        :param layers: the different working layers
        :return: the closest intersection as QgsPoint, or none
        """
        mousePoint = mapTool.toMapCoordinates(pixPoint)
        features = Finder.findFeaturesLayersAt(pixPoint, layers, mapTool)
        if features is None:
            return None
        nFeat = len(features)
        intersections = []
        for i in range(nFeat - 1):
            for j in range(i + 1, nFeat):
                geometry1 = features[i].geometry()
                geometry2 = features[j].geometry()
                if geometry1.type() == QGis.Polygon:
                    for curve1 in geometry1.asPolygon():
                        if geometry2.type() == QGis.Polygon:
                            for curve2 in geometry2.asPolygon():
                                intersect = Finder.intersect(QgsGeometry.fromPolyline(curve1), QgsGeometry.fromPolyline(curve2), mousePoint)
                                if intersect is not None:
                                    intersections.append(intersect)
                        else:
                            intersect = Finder.intersect(QgsGeometry.fromPolyline(curve1), geometry2, mousePoint)
                            if intersect is not None:
                                intersections.append(intersect)
                elif geometry2.type() == QGis.Polygon:
                    for curve2 in geometry2.asPolygon():
                        intersect = Finder.intersect(geometry1, QgsGeometry.fromPolyline(curve2), mousePoint)
                        if intersect is not None:
                            intersections.append(intersect)
                else:
                    intersect = Finder.intersect(geometry1, geometry2, mousePoint)
                    if intersect is not None:
                        intersections.append(intersect)
        if len(intersections) == 0:
            return None
        intersect = intersections[0]
        for point in intersections[1:]:
            if mousePoint.sqrDist(point) < mousePoint.sqrDist(intersect):
                intersect = QgsPoint(point.x(), point.y())
        return intersect

    @staticmethod
    def snapToLayers(pixPoint, snapperList, mapCanvas):
        """
        To snap on different layers
        :param pixPoint: the screen position
        :param snapperList: layers list to snap
        :param mapCanvas: canvas for the interface
        :return: the closest snapped point
        """
        if len(snapperList) == 0:
            return None
        snapper = QgsSnapper(mapCanvas.mapRenderer())
        snapper.setSnapLayers(snapperList)
        snapper.setSnapMode(QgsSnapper.SnapWithResultsWithinTolerances)
        ok, snappingResults = snapper.snapPoint(pixPoint, [])
        if ok == 0 and len(snappingResults) > 0:
            return QgsPoint(snappingResults[0].snappedVertex)
        else:
            return None
