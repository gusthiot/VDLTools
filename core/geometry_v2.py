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

from qgis.core import QgsPointV2, QgsLineStringV2


class GeometryV2:

    @staticmethod
    def asLineStringV2(geometry):
        wktLine = geometry.exportToWkt()
        if 'LineStringZ' not in wktLine:
            return None
        line = wktLine.replace('LineStringZ', '')
        line = line.replace(')', '')
        line = line.replace('(', '')
        points = line.split(',')
        if len(points) < 2:
            return None
        lineStringV2 = QgsLineStringV2()
        for pt in points:
            pt_tab = pt.strip().split()
            pointV2 = QgsPointV2(float(pt_tab[0]), float(pt_tab[1]))
            if len(pt_tab) > 2:
                pointV2.addZValue(float(pt_tab[2]))
            if len(pt_tab) > 3:
                pointV2.addMValue(float(pt_tab[3]))
            lineStringV2.addVertex(pointV2)
        return lineStringV2

    @staticmethod
    def asPointV2(geometry):
        wktPoint = geometry.exportToWkt()
        if 'PointZ' not in wktPoint:
            return None
        point = wktPoint.replace('PointZ', '')
        point = point.replace(')', '')
        point = point.replace('(', '')
        pt_tab = point.strip().split()
        pointV2 = QgsPointV2(float(pt_tab[0]), float(pt_tab[1]))
        if len(pt_tab) > 2:
            pointV2.addZValue(float(pt_tab[2]))
        if len(pt_tab) > 3:
            pointV2.addMValue(float(pt_tab[3]))
        return pointV2
