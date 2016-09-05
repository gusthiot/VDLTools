# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-09-05
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

from qgis.core import QgsPointV2
from math import (sqrt,
                  atan2)


class Circle:

    def __init__(self, point_1, point_2, point_3):
        self.__p1 = point_1
        self.__p2 = point_2
        self.__p3 = point_3

    def __mid_12(self):
        return QgsPointV2((self.__p1.x() + self.__p2.x())/2, (self.__p1.y() + self.__p2.y())/2)

    def __mid_23(self):
        return QgsPointV2((self.__p2.x() + self.__p3.x())/2, (self.__p2.y() + self.__p3.y())/2)

    def __slop_12(self):
        return (self.__p1.y() - self.__p2.y())/(self.__p1.x() - self.__p2.x())

    def __slop_23(self):
        return (self.__p2.y() - self.__p3.y()) / (self.__p2.x() - self.__p3.x())

    def __slop_p_12(self):
        return -1/self.__slop_12()

    def __slop_p_23(self):
        return -1/self.__slop_23()

    def center(self):
        mid_12 = self.__mid_12()
        mid_23 = self.__mid_23()
        slop_12 = self.__slop_p_12()
        slop_23 = self.__slop_p_23()
        x = (mid_23.y() - mid_12.y() + slop_12*mid_12.x() - slop_23*mid_23.x()) / (slop_12 - slop_23)
        y = (x - mid_12.x())*slop_12 + mid_12.y()
        return QgsPointV2(x, y)

    def radius(self):
        center = self.center()
        return sqrt(pow(self.__p1.x() - center.x(), 2) + pow(self.__p1.y() - center.y(), 2))

    def angle1(self):
        return self.angle(self.center(), self.__p1)

    def angle2(self):
        return self.angle(self.center(), self.__p2)

    def angle3(self):
        return self.angle(self.center(), self.__p3)

    @staticmethod
    def angle(point1, point2):
        """
        To calculate the angle of a line between 2 points
        :param point1: first point
        :param point2: second point
        :return: the calculated angle
        """
        return atan2(point2.y() - point1.y(), point2.x() - point1.x())