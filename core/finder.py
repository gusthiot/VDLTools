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


class Finder:

    @staticmethod
    def findClosestFeatureAt(pos, layer, mapTool, tolerance=10):
        features = Finder.findFeaturesAt(pos, layer, mapTool, tolerance)
        if features is not None and len(features) > 0:
            return features[0]
        else:
            return None

    @staticmethod
    def findClosestFeatureLayersAt(pos, layers, mapTool, tolerance=10):
        features = []
        for layer in layers:
            feats = Finder.findFeaturesAt(pos, layer, mapTool, tolerance)
            if feats is not None:
                for f in feats:
                    features.append([f, layer])
        if len(features) > 0:
            posP = QgsPoint(pos)
            dst = posP.sqrDist(features[0][0].geometry().asPoint())
            f = 0
            for i in xrange(1,len(features)):
                d = posP.sqrDist(features[i][0].geometry().asPoint())
                if d < dst:
                    dst = d
                    f = i
            return features[f]
        else:
            return None

    @staticmethod
    def findFeaturesLayersAt(pos, layers, mapTool, tolerance=10):
        features = []
        for layer in layers:
            features += Finder.findFeaturesAt(pos, layer, mapTool, tolerance)
        return features

    @staticmethod
    def findFeaturesAt(pos, layer, mapTool, tolerance):
        if layer is None:
            return None
        layerPt = mapTool.toLayerCoordinates(layer, pos)
        tolerance = Finder.calcTolerance(pos, layer, mapTool, tolerance)
        searchRect = QgsRectangle(layerPt.x() - tolerance, layerPt.y() - tolerance,
                                  layerPt.x() + tolerance, layerPt.y() + tolerance)
        request = QgsFeatureRequest()
        request.setFilterRect(searchRect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)
        features = []
        for feature in layer.getFeatures(request):
            features.append(QgsFeature(feature))
        return features

    @staticmethod
    def calcTolerance(pos, layer, mapTool, distance):
        pt1 = QPoint(pos.x(), pos.y())
        pt2 = QPoint(pos.x() + distance, pos.y())
        layerPt1 = mapTool.toLayerCoordinates(layer, pt1)
        layerPt2 = mapTool.toLayerCoordinates(layer, pt2)
        tolerance = layerPt2.x() - layerPt1.x()
        return tolerance

    @staticmethod
    def intersect(geometry1, geometry2, mousePoint):
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
