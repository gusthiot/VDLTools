# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-05-23
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

from qgis.core import QgsPointV2, QgsLineStringV2, QgsPolygonV2, QgsPoint


class GeometryV2:

    @staticmethod
    def asPolygonV2(geometry):
        wktPolygon = geometry.exportToWkt()
        if 'PolygonZ' in wktPolygon:
            polygon = wktPolygon.replace('PolygonZ', '')
        elif 'Polygon' in wktPolygon:
            polygon = wktPolygon.replace('Polygon', '')
        else:
            return None
        polygon = polygon.replace('))', '')
        polygon = polygon.replace('((', '')
        lines = polygon.split('),(')

        polygonV2 = QgsPolygonV2()
        polygonV2.setExteriorRing(GeometryV2.__createLine(lines[0].split(',')))
        if len(lines) > 1:
            for i in xrange(1, len(lines)):
                polygonV2.addInteriorRing(GeometryV2.__createLine(lines[i].split(',')))
        return polygonV2

    @staticmethod
    def asLineStringV2(geometry):
        wktLine = geometry.exportToWkt()
        if 'LineStringZ' in wktLine:
            line = wktLine.replace('LineStringZ', '')
        elif 'LineString' in wktLine:
            line = wktLine.replace('LineString', '')
        else:
            return None
        line = line.replace(')', '')
        line = line.replace('(', '')
        points = line.split(',')
        return GeometryV2.__createLine(points)

    @staticmethod
    def __createLine(tab):
        if len(tab) < 2:
            return None
        lineStringV2 = QgsLineStringV2()
        for pt in tab:
            pt_tab = pt.strip().split()
            lineStringV2.addVertex(GeometryV2.__createPoint(pt_tab))
        return lineStringV2

    @staticmethod
    def asPointV2(geometry):
        wktPoint = geometry.exportToWkt()
        if 'PointZ' in wktPoint:
            point = wktPoint.replace('PointZ', '')
        elif 'Point' in wktPoint:
            point = wktPoint.replace('Point', '')
        else:
            return None
        point = point.replace(')', '')
        point = point.replace('(', '')
        pt_tab = point.strip().split()
        return GeometryV2.__createPoint(pt_tab)

    @staticmethod
    def __createPoint(tab):
        pointV2 = QgsPointV2(float(tab[0]), float(tab[1]))
        if len(tab) > 2:
            pointV2.addZValue(float(tab[2]))
        if len(tab) > 3:
            pointV2.addMValue(float(tab[3]))
        return pointV2

    @staticmethod
    def sqrDist(pt1_v2, pt2_v2):
        pt1 = QgsPoint(pt1_v2.x(), pt1_v2.y())
        pt2 = QgsPoint(pt2_v2.x(), pt2_v2.y())
        return pt1.sqrDist(pt2)
