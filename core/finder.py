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
from qgis.core import QgsRectangle, QgsFeatureRequest, QgsFeature


class Finder:

    @staticmethod
    def findClosestFeatureAt(pos, layer, mapTool):
        features = Finder.findFeaturesAt(pos, layer, mapTool)
        if len(features) > 0 :
            return features[0]
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
