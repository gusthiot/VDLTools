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
from builtins import range
from builtins import object

from qgis.PyQt.QtCore import QPoint
from qgis.core import (QgsPoint,
                       QgsPointXY,
                       QgsWkbTypes,
                       QgsGeometry,
                       QgsMapLayer,
                       QgsTolerance,
                       QgsPointLocator,
                       QgsProject,
                       QgsSnappingConfig,
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
    def findClosestFeatureAt(mapPoint, mapCanvas, layers, type, tolerance, units):
        """
        To find closest feature from a given position in given layers
        :param mapPoint: the map position
        :param mapCanvas: the used QgsMapCanvas
        :return: feature found in layers
        """
        match = Finder.snapLayers(mapPoint, mapCanvas, layers, type, tolerance, units)
        if match.featureId() is not None and match.layer() is not None:
            print(match.layer().name())
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
        :param mapPoint: the XY map position
        :param layersConfig: the layers in which we are looking for features
        :param mapTool: a QgsMapTool instance
        :return: features found in layers
        """
        features = []
        for layer, config in layersConfig.items():
            features += Finder.findFeaturesAt(mapPoint, layer, config.tolerance, config.units, mapTool)
        return features

    @staticmethod
    def findFeaturesAt(mapPoint, layer, tolerance, units, mapTool):
        """
        To find features from a given position in a given layer
        :param mapPoint: the XY map position
        :param mapTool: a QgsMapTool instance
        :return: features found in layer
        """
        if units == QgsTolerance.Pixels:
            layTolerance = Finder.calcCanvasTolerance(mapTool.toCanvasCoordinates(mapPoint), layer, mapTool, tolerance)
        elif units == QgsTolerance.ProjectUnits:
            layTolerance = Finder.calcMapTolerance(mapPoint, layer, mapTool, tolerance)
        else:
            layTolerance = tolerance
        layPoint = mapTool.toLayerCoordinates(layer, mapPoint)
        searchRect = QgsRectangle(layPoint.x() - layTolerance, layPoint.y() - layTolerance,
                                  layPoint.x() + layTolerance, layPoint.y() + layTolerance)
        request = QgsFeatureRequest()
        request.setFilterRect(searchRect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)
        features = []
        for feature in layer.getFeatures(request):
            if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                dist, nearest, vertex = feature.geometry().closestSegmentWithContext(mapPoint)
                if QgsGeometry.fromPointXY(nearest).intersects(searchRect):
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
        pt1 = QgsPointXY(mapPoint.x(), mapPoint.y())
        pt2 = QgsPointXY(mapPoint.x() + distance, mapPoint.y())
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
            if geometry1.type() == 0:
                return geometry1.asPoint()
            if geometry2.type() == 0:
                return geometry2.asPoint()
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
                if (intersection.isMultipart()):
                    intersectionMP = intersection.asMultiPoint()
                    if intersectionMP is not None and len(intersectionMP) > 0:
                        for point in intersectionMP:
                            if intersectionP is None:
                                intersectionP = point
                            elif mousePoint.sqrDist(point) < mousePoint.sqrDist(intersectionP):
                                intersectionP = QgsPoint(point.x(), point.y())
            elif intersection.type() == 1:
                intersectionPL = intersection.asPolyline()
                intersectionP = None
                if (intersection.isMultipart()):
                    intersectionMPL = intersection.asMultiPolyline()
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
                intersectionP = None
                if (intersection.isMultipart()):
                    intersectionMPL = intersection.asMultiPolyline()
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
        snap_layers = {}
        for layer in mapCanvas.layers():
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() in types:
                snap_util = mapCanvas.snappingUtils()
                mode = snap_util.config().mode()
                if mode == QgsSnappingConfig.ActiveLayer and layer.id() != mapCanvas.currentLayer().id():
                    continue
                if mode == QgsSnappingConfig.AllLayers:
                    individual = snap_util.config().individualLayerSettings(layer)
                    snap_type = individual.type()
                    tolerance = individual.tolerance()
                    unitType = individual.units()
                else:
                    noUse, enabled, snappingType, unitType, tolerance, avoidIntersection = \
                        QgsProject.instance().snapSettingsForLayer(layer.id())
                    if layer.type() == QgsMapLayer.VectorLayer and enabled:
                        if snapType is None:
                            snap_type = snappingType
                        else:
                            snap_type = snapType
                    else:
                        continue
                snap_layers[layer] = {'type': snap_type, 'tolerance': tolerance, 'units': unitType}
        return snap_layers

    # @staticmethod
    # def snappingConfigToLocatorType(snappingType):
    #         if snappingType == QgsSnappingConfig.Vertex:
    #             return QgsPointLocator.Vertex
    #         elif snappingType == QgsSnappingConfig.Segment:
    #             return QgsPointLocator.Edge
    #         elif snappingType == QgsSnappingConfig.VertexAndSegment:
    #             return QgsPointLocator.Edge and QgsPointLocator.Vertex
    #         else:
    #             return QgsPointLocator.All

    @staticmethod
    def snapCurvedIntersections(mapPoint, mapCanvas, mapTool, featureId=None):
        """
        To snap on curved intersections
        :param mapPoint: the XY map position
        :param mapCanvas: the used QgsMapCanvas
        :param mapTool: a QgsMapTool instance
        :param featureId: if we want to snap on a given feature
        :return: intersection point
        """
        snap_layers = Finder.getLayersSettings(mapCanvas, [QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry, QgsWkbTypes.PointGeometry])
        features = Finder.findFeaturesLayersAt(mapPoint, snap_layers, mapTool)
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
    def snapLayersConfigs(mapPoint, mapCanvas, layersConfigs=None):
        snap_util = mapCanvas.snappingUtils()
        config = snap_util.config()
        for lay, iConf in config.individualLayerSettings().items():
            if lay in layersConfigs:
                iConf.setTolerance(layersConfigs[lay].tolerance)
                iConf.setType(layersConfigs[lay].type)
                iConf.setUnits(layersConfigs[lay].units)
                iConf.setEnabled(True)
            else:
                iConf.setEnabled(False)
            config.setIndividualLayerSettings(lay, iConf)
        snap_util.setConfig(config)
        match = snap_util.snapToMap(mapPoint)
        config.reset()
        snap_util.setConfig(config)
        return match


    @staticmethod
    def snapLayers(mapPoint, mapCanvas, layers, sType, tolerance, units):
        snap_util = mapCanvas.snappingUtils()
        config = snap_util.config()

        for conf in snap_util.layers():
            print("a", conf.layer.name())
        #for lay, iConf in config.individualLayerSettings().items():
        #    print("1", lay.name(), iConf.enabled())
        for lay, iConf in config.individualLayerSettings().items():
            if lay in layers:
                iConf.setTolerance(tolerance)
                # iConf.setType(sType)
                iConf.setUnits(units)
                iConf.setEnabled(True)
            else:
                iConf.setEnabled(False)
            config.setIndividualLayerSettings(lay, iConf)
        #for lay, iConf in snap_util.config().individualLayerSettings().items():
        #    print("2", lay.name(), iConf.enabled())
        snap_util.setConfig(config)
        for conf in snap_util.layers():
            print("b", conf.layer.name(), conf.type, conf.tolerance, conf.unit)
        #print(config.mode())
        match = snap_util.snapToMap(mapPoint)
        config.reset()
        #print(config.mode())
        snap_util.setConfig(config)
        return match
