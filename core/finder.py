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
                       QgsRectangle,
                       QgsFeatureRequest,
                       QgsFeature)


class Finder:

    @staticmethod
    def findClosestFeatureAt(pos, layer, mapTool):
        features = Finder.findFeaturesAt(pos, layer, mapTool)
        if features is not None and len(features) > 0:
            return features[0]
        else:
            return None

    @staticmethod
    def findClosestFeatureLayersAt(pos, layers, mapTool):
        features = []
        for layer in layers:
            feats = Finder.findFeaturesAt(pos, layer, mapTool)
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
    def findFeaturesLayersAt(pos, layers, mapTool):
        features = []
        for layer in layers:
            features += Finder.findFeaturesAt(pos, layer, mapTool)
        return features

    @staticmethod
    def findFeaturesAt(pos, layer, mapTool):
        if layer is None:
            return None
        mapPt, layerPt = Finder.transformCoordinates(pos, layer, mapTool)
        tolerance = Finder.calcTolerance(pos, layer, mapTool)
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
    def transformCoordinates(screenPt, layer, mapTool):
        return mapTool.toMapCoordinates(screenPt), mapTool.toLayerCoordinates(layer, screenPt)

    @staticmethod
    def calcTolerance(pos, layer, mapTool):
        pt1 = QPoint(pos.x(), pos.y())
        pt2 = QPoint(pos.x() + 10, pos.y())
        mapPt1, layerPt1 = Finder.transformCoordinates(pt1, layer, mapTool)
        mapPt2, layerPt2 = Finder.transformCoordinates(pt2, layer, mapTool)
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
