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
from __future__ import print_function
from builtins import range
from builtins import object

from qgis.core import (QgsPointV2,
                       QgsVertexId,
                       QgsCompoundCurveV2,
                       QgsLineStringV2,
                       QgsCurvePolygonV2,
                       QgsCircularStringV2)


class GeometryV2(object):
    """
    Class to replace QgsFeature geometry().geometry() that is crashing
    """

    @staticmethod
    def asPolygonV2(geometry):
        """
        To get the feature geometry from a polygon as a QgsCurvePolygonV2
        :param geometry: the feature geometry
        :return: the polygon as QgsCurvePolygonV2 , and true if it has curves or false if it hasn't, or none
        """
        wktPolygon = geometry.exportToWkt()
        curved = []
        if wktPolygon.startswith('PolygonZ'):
            polygon = wktPolygon.replace('PolygonZ', '')
        elif wktPolygon.startswith('Polygon'):
            polygon = wktPolygon.replace('Polygon', '')
        elif wktPolygon.startswith('CurvePolygonZ'):
            polygon = wktPolygon.replace('CurvePolygonZ', '')
        elif wktPolygon.startswith('CurvePolygon'):
            polygon = wktPolygon.replace('CurvePolygon', '')
        else:
            print("This geometry is not yet implemented")
            return None
        polygon = polygon.strip()[1:-1]
        lines = polygon.split('),')
        polygonV2 = QgsCurvePolygonV2()
        for i in range(0, len(lines)):
            line = lines[i]
            if line.startswith('CircularStringZ'):
                curved.append(True)
                line = line.replace('CircularStringZ', '')
            elif line.startswith('CircularString'):
                curved.append(True)
                line = line.replace('CircularString', '')
            else:
                curved.append(False)
            line = line.strip()[1:-1]

            if i == 0:
                polygonV2.setExteriorRing(GeometryV2.__createLine(line.split(','), curved[i]))
            else:
                polygonV2.addInteriorRing(GeometryV2.__createLine(line.split(','), curved[i]))
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
        if wktLine.startswith('LineStringZ'):
            line = wktLine.replace('LineStringZ', '')
        elif wktLine.startswith('LineString'):
            line = wktLine.replace('LineString', '')
        elif wktLine.startswith('CircularStringZ'):
            curved = True
            line = wktLine.replace('CircularStringZ', '')
        elif wktLine.startswith('CircularString'):
            curved = True
            line = wktLine.replace('CircularString', '')
        else:
            if wktLine.startswith('CompoundCurveZ'):
                compound = wktLine.replace('CompoundCurveZ', '')
            elif wktLine.startswith('CompoundCurve'):
                compound = wktLine.replace('CompoundCurve', '')
            else:
                print("This geometry is not yet implemented")
                return None
            compound = compound.strip()[1:-1]
            lines = compound.split('),')
            compoundV2 = QgsCompoundCurveV2()
            curved = []
            for i in range(0, len(lines)):
                line = lines[i]
                if line.startswith('CircularStringZ'):
                    curved.append(True)
                    line = line.replace('CircularStringZ', '')
                elif line.startswith('CircularString'):
                    curved.append(True)
                    line = line.replace('CircularString', '')
                else:
                    curved.append(False)
                line = line.strip()[1:-1]

                compoundV2.addCurve(GeometryV2.__createLine(line.split(','), curved[i]))
            return compoundV2, curved

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
        if wktPoint.startswith('PointZ'):
            point = wktPoint.replace('PointZ', '')
        elif wktPoint.startswith('Point'):
            point = wktPoint.replace('Point', '')
        else:
            print("This geometry is not yet implemented")
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

    @staticmethod
    def polygonVertexId(polygon_v2, vertex_id):
        """
        To get the id of the selected vertex from a polygon
        :param polygon_v2: the polygon as polygonV2
        :param vertex_id: selected vertex
        :return: id as QgsVertexId
        """
        eR = polygon_v2.exteriorRing()
        if vertex_id < eR.numPoints():
            return QgsVertexId(0, 0, vertex_id, 1)
        else:
            sel = vertex_id - eR.numPoints()
            for num in range(polygon_v2.numInteriorRings()):
                iR = polygon_v2.interiorRing(num)
                if sel < iR.numPoints():
                    return QgsVertexId(0, num + 1, sel, 1)
                sel -= iR.numPoints()
