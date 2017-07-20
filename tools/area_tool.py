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
        self.__clear()


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
            firstV2 = QgsPointV2(self.first)
            second = QgsPointV2(self.first.x(), event.mapPoint().y())
            third = QgsPointV2(event.mapPoint())
            fourth = QgsPointV2(event.mapPoint().x(), self.first.y())

            lineV2 = QgsLineStringV2()
            lineV2.setPoints([firstV2, second, third, fourth, firstV2])
            polygonV2 = QgsPolygonV2()
            polygonV2.setExteriorRing(lineV2)
            self.geom = QgsGeometry(polygonV2)
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
