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

from qgis.core import (QgsPointV2,
                       QgsLineStringV2,
                       QgsCurvePolygonV2,
                       QgsCircularStringV2)


class GeometryV2:

    @staticmethod
    def asPolygonV2(geometry):
        """
        To get the feature geometry from a polygon as a QgsCurvePolygonV2
        (as soon as the geometry().geometry() is crashing)
        :param geometry: the feature geometry
        :return: the polygon as QgsCurvePolygonV2 , and true if it has curves or false if it hasn't, or none
        """
        wktPolygon = geometry.exportToWkt()
        curved = False
        if 'PolygonZ' in wktPolygon:
            polygon = wktPolygon.replace('PolygonZ', '')
        elif 'Polygon' in wktPolygon:
            polygon = wktPolygon.replace('Polygon', '')
        elif 'CurvePolygon Z' in wktPolygon:
            curved = True
            polygon = wktPolygon.replace('CurvePolygon Z', '')
        elif 'CurvePolygon ' in wktPolygon:
            curved = True
            polygon = wktPolygon.replace('CurvePolygon', '')
        else:
            print "This geometry is not yet implemented"
            return None
        polygon = polygon.strip()[1:-1]
        lines = polygon.split('),')
        polygonV2 = QgsCurvePolygonV2()
        for i in xrange(0, len(lines)):
            line = lines[i]
            if 'CircularString Z' in line:
                curved = True
                line = line.replace('CircularString Z', '')
            elif 'CircularString ' in line:
                curved = True
                line = line.replace('CircularString', '')
            line = line.replace('(', "")

            if i == 0:
                polygonV2.setExteriorRing(GeometryV2.__createLine(line.split(','), curved))
            else:
                polygonV2.addInteriorRing(GeometryV2.__createLine(line.split(','), curved))
        return polygonV2, curved

    @staticmethod
    def asLineV2(geometry):
        """
        To get the feature geometry from a line as a QgsLineStringV2/QgsCircularStringV2
        (as soon as the geometry().geometry() is crashing)
        :param geometry: the feature geometry
        :return: the line as QgsLineStringV2/QgsCircularStringV2 , and true if it has curves or false if it hasn't,
        or none
        """
        wktLine = geometry.exportToWkt()
        curved = False
        if 'LineStringZ' in wktLine:
            line = wktLine.replace('LineStringZ', '')
        elif 'LineString' in wktLine:
            line = wktLine.replace('LineString', '')
        elif 'CircularString Z' in wktLine:
            curved = True
            line = wktLine.replace('CircularString Z', '')
        elif 'CircularString ' in wktLine:
            curved = True
            line = wktLine.replace('CircularString', '')
        else:
            print "This geometry is not yet implemented"
            return None
        line = line.strip()[1:-1]
        points = line.split(',')
        return GeometryV2.__createLine(points, curved), curved

    @staticmethod
    def __createLine(tab, curved):
        """
        To create a new line V2 from a list of points coordinates
        :param tab: list of points coordinates
        :param curved: true if it has curves, false if it hasn't
        :return: the new line as QgsLineStringV2/QgsCircularStringV2, or none
        """
        if len(tab) < 2:
            return None
        points = []
        for pt in tab:
            pt_tab = pt.strip().split()
            points.append(GeometryV2.__createPoint(pt_tab))
        if curved:
            lineV2 = QgsCircularStringV2()
        else:
            lineV2 = QgsLineStringV2()
        lineV2.setPoints(points)
        return lineV2

    @staticmethod
    def asPointV2(geometry):
        """
        To get the feature geometry from a line as a QgsPointV2
        (as soon as the geometry().geometry() is crashing)
        :param geometry: the feature geometry
        :return: the point as QgsPointV2, or none
        """
        wktPoint = geometry.exportToWkt()
        if 'PointZ' in wktPoint:
            point = wktPoint.replace('PointZ', '')
        elif 'Point' in wktPoint:
            point = wktPoint.replace('Point', '')
        else:
            return None
        point = point.strip()[1:-1]
        pt_tab = point.strip().split()
        return GeometryV2.__createPoint(pt_tab)

    @staticmethod
    def __createPoint(tab):
        """
        To create a new QGSPointV2 from coordinates
        :param tab: coordinates
        :return: QGSPointV2
        """
        pointV2 = QgsPointV2(float(tab[0]), float(tab[1]))
        if len(tab) > 2:
            pointV2.addZValue(float(tab[2]))
        if len(tab) > 3:
            pointV2.addMValue(float(tab[3]))
        return pointV2
