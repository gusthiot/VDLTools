# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2017-01-09
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
from qgis.core import (QgsPoint,
                       QgsWkbTypes,
                       QgsLineString,
                       QgsGeometry)
from qgis.gui import (QgsMapTool,
                      QgsRubberBand)
from qgis.PyQt.QtCore import (Qt,
                              QCoreApplication)
from qgis.PyQt.QtGui import QColor
from ..ui.profile_dock_widget import ProfileDockWidget


class SubProfileTool(QgsMapTool):
    """
    Tool class for making a line elevation profile
    """

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.icon_path = ':/plugins/VDLTools/icons/profile_2_icon.png'
        self.text = QCoreApplication.translate("VDLTools", "Line for MNT profile")
        self.setCursor(Qt.ArrowCursor)
        self.__isSelected = False
        self.__dockWdg = None
        self.__rubberLine = None
        self.__rubberDots = None
        self.ownSettings = None
        self.__line = None
        self.__startVertex = None
        self.__isfloating = False
        self.__dockGeom = None

    def setTool(self):
        """
        To set the current tool as this one
        """
        self.canvas().setMapTool(self)

    def activate(self):
        """
        When the action is selected
        """
        QgsMapTool.activate(self)
        self.__dockWdg = ProfileDockWidget(self.__iface, self.__dockGeom)
        if self.__isfloating:
            self.__dockWdg.show()
        else:
            self.__iface.addDockWidget(Qt.BottomDockWidgetArea, self.__dockWdg)
        self.__dockWdg.closeSignal.connect(self.__closed)
        self.__rubberLine = QgsRubberBand(self.canvas(), QgsWkbTypes.LineGeometry)
        color = QColor("red")
        color.setAlphaF(0.78)
        self.__rubberLine.setColor(color)
        self.__rubberDots = QgsRubberBand(self.canvas(), QgsWkbTypes.LineGeometry)
        color = QColor("red")
        color.setAlphaF(0.78)
        self.__rubberDots.setColor(color)
        self.__rubberDots.setLineStyle(Qt.DotLine)

    def __closed(self):
        """
        When the dock is closed
        """
        self.__dockGeom = self.__dockWdg.geometry()
        self.__isfloating = self.__dockWdg.isFloating()
        self.__cancel()
        self.__iface.actionPan().trigger()

    def deactivate(self):
        """
        When the action is deselected
        """
        self.canvas().scene().removeItem(self.__rubberLine)
        self.__rubberLine = None
        if self.__dockWdg is not None:
            self.__dockWdg.close()
        QgsMapTool.deactivate(self)

    def __cancel(self):
        """
        To cancel used variables
        """
        self.__isSelected = False
        self.__rubberDots = None
        self.__line = None
        self.__startVertex = None

    def keyReleaseEvent(self, event):
        """
        When keyboard is pressed
        :param event: keyboard event
        """
        if event.key() == Qt.Key_Escape:
            self.__cancel()

    def canvasMoveEvent(self, event):
        """
        When the mouse is moved
        :param event: mouse event
        """
        if self.__isSelected:
            dots = QgsLineString()
            dots.addVertex(self.__startVertex)
            dots.addVertex(QgsPoint(event.mapPoint()))
            self.__rubberDots.reset()
            self.__rubberDots.setToGeometry(QgsGeometry(dots.clone()), None)

    def canvasReleaseEvent(self, event):
        """
        When the mouse is clicked
        :param event: mouse event
        """
        if event.button() == Qt.RightButton:
            self.__isSelected = False
            self.__rubberDots.reset()
            self.__calculateProfile()

        elif event.button() == Qt.LeftButton:
            if not self.__isSelected:
                self.__isSelected = True
                self.__dockWdg.clearData()
                self.__line = QgsLineString()
                self.__rubberLine.reset()
            self.__startVertex = QgsPoint(event.mapPoint())
            self.__line.addVertex(self.__startVertex)
            if self.__isSelected:
                self.__rubberLine.reset()
                self.__rubberLine.setToGeometry(QgsGeometry(self.__line.clone()), None)

    def __calculateProfile(self):
        """
        To calculate the profile and display it
        """
        if self.__line is None:
            return
        self.__dockWdg.clearData()
        if self.__line.numPoints() == 0:
            return
        points = []
        for i in range(self.__line.numPoints()):
            points.append({'x': self.__line.pointN(i).x(), 'y': self.__line.pointN(i).y()})
        self.__dockWdg.setProfiles(points, 0)
        self.__dockWdg.attachCurves(None, self.ownSettings, [1, 1, 1])
