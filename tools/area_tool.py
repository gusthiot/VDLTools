# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2017-02-14
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
from __future__ import division
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QColor
from qgis.gui import (QgsMapTool,
                      QgsRubberBand)
from qgis.core import (QGis,
                       QgsLineStringV2,
                       QgsPolygonV2,
                       QgsPointV2,
                       QgsGeometry)


class AreaTool(QgsMapTool):
    """
    Map tool class to select an area
    """

    releasedSignal = pyqtSignal()

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__selecting = False
        self.__first = None
        self.__last = None
        self.__temp = None
        self.__rubber = None
        self.__geom = None

    def activate(self):
        """
        When the action is selected
        """
        QgsMapTool.activate(self)
        self.__rubber = QgsRubberBand(self.canvas(), QGis.Polygon)
        color = QColor("red")
        color.setAlphaF(0.6)
        self.__rubber.setBorderColor(color)
        color = QColor("orange")
        color.setAlphaF(0.3)
        self.__rubber.setFillColor(color)

    def deactivate(self):
        """
        When the action is deselected
        """
        self.__rubber = None
        self.__selecting = False
        self.__first = None
        self.__last = None
        self.__temp = None
        self.__geom = None
        QgsMapTool.deactivate(self)

    def geom(self):
        return self.__geom

    def first(self):
        return self.__first

    def last(self):
        return self.__last

    def canvasMoveEvent(self, event):
        if self.__selecting:
            self.__temp = event.mapPoint()
            self.__rubber.reset()
            first = QgsPointV2(self.__first.x(), self.__first.y())
            second = QgsPointV2(self.__first.x(), self.__temp.y())
            third = QgsPointV2(self.__temp.x(), self.__temp.y())
            forth = QgsPointV2(self.__temp.x(), self.__first.y())

            lineV2 = QgsLineStringV2()
            lineV2.setPoints([first, second, third, forth, first])
            polygonV2 = QgsPolygonV2()
            polygonV2.setExteriorRing(lineV2)
            self.__geom = QgsGeometry(polygonV2)
            self.__rubber.setToGeometry(self.__geom, None)

    def canvasPressEvent(self, event):
        self.__selecting = True
        self.__first = event.mapPoint()

    def canvasReleaseEvent(self, event):
        self.__selecting = False
        self.__last = event.mapPoint()
        self.__rubber.reset()
        self.releasedSignal.emit()
