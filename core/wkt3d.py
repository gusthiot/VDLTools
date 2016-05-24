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


class Wkt3d:

    @staticmethod
    def wkt3dLine(wktLine):
        if 'LineStringZ' not in wktLine:
            return None
        line = wktLine.replace('LineStringZ', '')
        line = line.replace(')', '')
        line = line.replace('(', '')
        points = line.split(',')
        if len(points) < 2:
            return None
        pointsZ = []
        for pt in points:
            pt_tab = pt.strip().split()
            pt_num = []
            for p in pt_tab:
                pt_num.append(float(p))
            pointsZ.append(pt_num)
        return pointsZ

    @staticmethod
    def wkt3dPoint(wktPoint):
        if 'PointZ' not in wktPoint:
            return None
        point = wktPoint.replace('PointZ', '')
        point = point.replace(')', '')
        point = point.replace('(', '')
        pt_tab = point.strip().split()
        pt_num = []
        for p in pt_tab:
            pt_num.append(float(p))
        return pt_num
