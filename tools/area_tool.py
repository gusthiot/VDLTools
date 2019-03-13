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
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import (QgsLineString,
                       QgsPolygon,
                       QgsPoint,
                       QgsWkbTypes,
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
        self.__clear()


    def activate(self):
        """
        When the action is selected
        """
        QgsMapTool.activate(self)
        self.__rubber = QgsRubberBand(self.canvas(), QgsWkbTypes.PolygonGeometry)
        color = QColor("red")
        color.setAlphaF(0.6)
        self.__rubber.setColor(color)
        color = QColor("orange")
        color.setAlphaF(0.3)
        self.__rubber.setFillColor(color)

    def deactivate(self):
        """
        When the action is deselected
        """
        self.__clear()
        QgsMapTool.deactivate(self)

    def __clear(self):
        """
        To clear used variables
        """
        self.__selecting = False
        self.__rubber = None
        self.first = None
        self.last = None
        self.geom = None

    def canvasMoveEvent(self, event):
        """
        When the mouse is moved
        :param event: mouse event
        """
        if self.__selecting:
            self.__rubber.reset()
            firstZ = QgsPoint(self.first)
            second = QgsPoint(self.first.x(), event.mapPoint().y())
            third = QgsPoint(event.mapPoint())
            fourth = QgsPoint(event.mapPoint().x(), self.first.y())

            line = QgsLineString()
            line.setPoints([firstZ, second, third, fourth, firstZ])
            polygon = QgsPolygon()
            polygon.setExteriorRing(line)
            self.geom = QgsGeometry(polygon)
            self.__rubber.setToGeometry(self.geom, None)

    def canvasPressEvent(self, event):
        """
        When the mouse is pressed
        :param event: mouse event
        """
        self.__selecting = True
        self.first = event.mapPoint()

    def canvasReleaseEvent(self, event):
        """
        When the mouse is clicked
        :param event: mouse event
        """
        self.__selecting = False
        self.last = event.mapPoint()
        self.__rubber.reset()
        self.releasedSignal.emit()
