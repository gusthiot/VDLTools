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
                       QgsVectorLayer,
                       QgsTolerance,
                       QgsMapLayer,QgsPointLocator,
                       QgsMapSettings,
                       QgsProject,
                       QgsSnapper,
                       QgsGeometry,
                       QgsSnappingUtils,
                       QgsRectangle,
                       QgsFeatureRequest,
                       QgsFeature)
from math import (sqrt,
                  pow)


class Finder:

    @staticmethod
    def findClosestFeatureAt(mapPoint, layerConfig, mapTool):
        """
        To find the closest feature from a given position in a given layer
        :param mapPoint: the map position
        :param layerConfig: the layer in which we are looking for features
        :param mapTool: a QgsMapTool instance
        :return: closest feature found or none
        """
        features = Finder.findFeaturesAt(mapPoint, layerConfig, mapTool)
        if features is not None and len(features) > 0:
            return features[0]
        else:
            return None

    @staticmethod
    def findClosestFeatureLayersAt(mapPoint, layersConfig, mapTool):
        """
        To find the closest feature from a given position in given layers
        :param mapPoint: the map position
        :param layersConfig: the layers in which we are looking for features
        :param mapTool: a QsMapTool instance
        :return: closest feature found or none
        """
        features = []
        for layerConfig in layersConfig:
            feats = Finder.findFeaturesAt(mapPoint, layerConfig, mapTool)
            if feats is not None:
                for f in feats:
                    features.append([f, layerConfig.layer])
        if len(features) > 0:
            dst = Finder.sqrDistForPoints(mapPoint, features[0][0].geometry().asPoint())
            f = 0
            for i in xrange(1,len(features)):
                d = Finder.sqrDistForPoints(mapPoint, features[i][0].geometry().asPoint())
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
            layerFeatures = Finder.findFeaturesAt(mapPoint, layerConfig, mapTool)
            if len(layerFeatures)>0:
                for f in layerFeatures:
                    features.append([f, layerConfig.layer])
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
            layTolerance = Finder.calcCanvasTolerance(mapTool.toCanvasCoordinates(mapPoint), layerConfig.layer, mapTool, tolerance)
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
    #
    # @staticmethod
    # def snapToIntersection(mapPoint, mapTool, layers):
    #     """
    #     To find the closest intersection in different layers for a given point
    #     :param mapPoint: the map position
    #     :param mapTool: a QgsMapTool instance
    #     :param layers: the different working layers
    #     :return: the closest intersection as QgsPoint, or none
    #     """
    #     print("nb layers intersects : " + str(len(layers)))
    #     features = Finder.findFeaturesLayersAt(mapPoint, layers, mapTool)
    #     if features is None:
    #         return None
    #     nFeat = len(features)
    #     print("nb interesects : " + str(nFeat))
    #     intersections = []
    #     for i in range(nFeat - 1):
    #         for j in range(i + 1, nFeat):
    #             geometry1 = features[i].geometry()
    #             geometry2 = features[j].geometry()
    #             if geometry1.type() == QGis.Polygon:
    #                 for curve1 in geometry1.asPolygon():
    #                     if geometry2.type() == QGis.Polygon:
    #                         for curve2 in geometry2.asPolygon():
    #                             intersect = Finder.intersect(QgsGeometry.fromPolyline(curve1), QgsGeometry.fromPolyline(curve2), mapPoint)
    #                             if intersect is not None:
    #                                 intersections.append(intersect)
    #                     else:
    #                         intersect = Finder.intersect(QgsGeometry.fromPolyline(curve1), geometry2, mapPoint)
    #                         if intersect is not None:
    #                             intersections.append(intersect)
    #             elif geometry2.type() == QGis.Polygon:
    #                 for curve2 in geometry2.asPolygon():
    #                     intersect = Finder.intersect(geometry1, QgsGeometry.fromPolyline(curve2), mapPoint)
    #                     if intersect is not None:
    #                         intersections.append(intersect)
    #             else:
    #                 intersect = Finder.intersect(geometry1, geometry2, mapPoint)
    #                 if intersect is not None:
    #                     intersections.append(intersect)
    #     if len(intersections) == 0:
    #         return None
    #     intersect = intersections[0]
    #     for point in intersections[1:]:
    #         if mapPoint.sqrDist(point) < mapPoint.sqrDist(intersect):
    #             intersect = QgsPoint(point.x(), point.y())
    #     print("return intersect")
    #     return intersect
    #
    # @staticmethod
    # def snapToLayers(mapPoint, snapperList):
    #     """
    #     To snap on different layers
    #     :param mapPoint: the map position
    #     :param snapperList: layers list to snap
    #     :return: the closest snapped point
    #     """
    #     print("nb layers snap : " + str(len(snapperList)))
    #     if len(snapperList) == 0:
    #         return None
    #     snapper = QgsSnapper(QgsMapSettings())
    #     snapper.setSnapLayers(snapperList)
    #     snapper.setSnapMode(QgsSnapper.SnapWithResultsWithinTolerances)
    #     ok, snappingResults = snapper.snapMapPoint(mapPoint, [])
    #     print("nb snap : " + str(len(snappingResults)))
    #     if ok == 0 and len(snappingResults) > 0:
    #         return QgsPoint(snappingResults[0].snappedVertex)
    #     else:
    #         return None
    #
    # @staticmethod
    # def updateSnapperList(iface):
    #     """
    #     To update the list of layers that can be snapped
    #     :param iface: interface
    #     """
    #     snapperList = []
    #     layerList = []
    #     legend = iface.legendInterface()
    #     scale = iface.mapCanvas().scale()
    #     for layer in iface.mapCanvas().layers():
    #         # noUse, enabled, snappingType, unitType, tolerance, avoidIntersection = \
    #         #    QgsProject.instance().snapSettingsForLayer(layer.id())
    #         if layer.type() == QgsMapLayer.VectorLayer and layer.hasGeometryType():
    #             if not layer.hasScaleBasedVisibility() or layer.minimumScale() < scale <= layer.maximumScale():
    #                 if legend.isLayerVisible(layer): # and enabled:
    #                     snapLayer = QgsSnapper.SnapLayer()
    #                     snapLayer.mLayer = layer
    #                     snapLayer.mSnapTo = QgsSnapper.SnapToVertex  # snappingType
    #                     snapLayer.mTolerance = 7  # tolerance
    #                     snapLayer.mUnitType = QgsTolerance.Pixels  # unitType
    #                     snapperList.append(snapLayer)
    #                     laySettings = {'layer': layer, 'tolerance': 7, 'unitType': QgsTolerance.Pixels}
    #                     layerList.append(laySettings)
    #     return snapperList, layerList

    @staticmethod
    def snapCurvedIntersections(mapPoint, mapCanvas, mapTool, checkForAFeature=False, featureId=None):
        snap_layers = []
        for layer in mapCanvas.layers():
            if isinstance(layer, QgsVectorLayer):
                noUse, enabled, snappingType, unitType, tolerance, avoidIntersection = QgsProject.instance().snapSettingsForLayer(layer.id())
                if isinstance(layer, QgsVectorLayer) and enabled:
                    if snappingType == QgsSnapper.SnapToVertex:
                        snap_type = QgsPointLocator.Vertex
                    elif snappingType == QgsSnapper.SnapToSegment:
                        snap_type = QgsPointLocator.Edge
                    else:
                        snap_type = QgsPointLocator.All
                    snap_layers.append(QgsSnappingUtils.LayerConfig(layer, snap_type, tolerance, unitType))

        featuresL = Finder.findFeaturesLayersAt(mapPoint, snap_layers, mapTool)
        features = []
        for f in featuresL:
            features.append(f[0])
        if len(features) > 1:
            display = ""
            for f in featuresL:
                display += str(f[0].id()) + " - " + f[1].name() + " | "
            display += "| "
            print(display)
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
            if not checkForAFeature or feat1.id() == featureId or feat2.id() == featureId:
                print (feat1.id(), feat1.geometry(), feat2.id(), feat2.geometry())
                return Finder.intersect(feat1.geometry(), feat2.geometry(), mapPoint)
            else:
                return None
        else:
            return None

    @staticmethod
    def snap(mapPoint, mapCanvas, snapIntersections):

        snap_layers = []
        for layer in mapCanvas.layers():
            if isinstance(layer, QgsVectorLayer):
                noUse, enabled, snappingType, unitType, tolerance, avoidIntersection = QgsProject.instance().snapSettingsForLayer(layer.id())
                if isinstance(layer, QgsVectorLayer) and enabled:
                    if snappingType == QgsSnapper.SnapToVertex:
                        snap_type = QgsPointLocator.Vertex
                    elif snappingType == QgsSnapper.SnapToSegment:
                        snap_type = QgsPointLocator.Edge
                    else:
                        snap_type = QgsPointLocator.All
                    snap_layers.append(QgsSnappingUtils.LayerConfig(layer, snap_type, tolerance, unitType))

        snap_util = mapCanvas.snappingUtils()
        old_layers = snap_util.layers()
        old_mode = snap_util.snapToMapMode()
        old_inter = snap_util.snapOnIntersections()
        snap_util.setLayers(snap_layers)
        snap_util.setSnapToMapMode(QgsSnappingUtils.SnapAdvanced)
        snap_util.setSnapOnIntersections(snapIntersections)
        match = snap_util.snapToMap(mapPoint)
        snap_util.setLayers(old_layers)
        snap_util.setSnapToMapMode(old_mode)
        snap_util.setSnapOnIntersections(old_inter)

        return match
