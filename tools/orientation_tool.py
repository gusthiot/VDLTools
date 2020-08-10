# -*- coding: utf-8 -*-

#-----------------------------------------------------------
#
# Intersect It is a QGIS plugin to place observations (distance or orientation)
# with their corresponding precision, intersect them using a least-squares solution
# and save dimensions in a dedicated layer to produce maps.
#
# Copyright    : (C) 2013 Denis Rouzaud
# Email        : denis.rouzaud@gmail.com
#
#-----------------------------------------------------------
#
# licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#---------------------------------------------------------------------
"""
Reimplemented for QGIS3 by :

/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2020-08-07
        git sha              : $Format:%H$
        copyright            : (C) 2020 Ville de Lausanne
        author               : Christophe Gusthiot
        email                : i2g@gusthiot.ch
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import (Qt,
                              QCoreApplication)
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsGeometry,
                       QgsWkbTypes,
                       QgsPoint,
                       QgsCircularString,
                       QgsFeature,
                       QgsProject,
                       QgsVectorLayer)
from qgis.gui import (QgsMapTool,
                      QgsRubberBand)
from ..ui.orientation_dialog import OrientationDialog
from ..core.orientation import Orientation


class OrientationTool(QgsMapTool):
    """
    Map tool class to
    """

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.icon_path = ':/plugins/VDLTools/icons/orientation_icon.png'
        self.text = QCoreApplication.translate("VDLTools", "Place orientation")
        self.setCursor(Qt.ArrowCursor)
        self.__rubber = None
        self.ownSettings = None

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
        self.__rubber = QgsRubberBand(self.canvas(), QgsWkbTypes.LineGeometry)
        color = QColor("blue")
        color.setAlphaF(0.78)
        self.__rubber.setColor(color)
        self.__rubber.setWidth(2)
        self.__rubber.setLineStyle(Qt.DashLine)

    def deactivate(self):
        """
        When the action is deselected
        """
        self.__cancel()
        self.__rubber = None
        QgsMapTool.deactivate(self)

    def __cancel(self):
        """
        To cancel used variables
        """
        if self.__rubber is not None:
            self.__rubber.reset()

    def canvasPressEvent(self, mouseEvent):
        if mouseEvent.button() != Qt.LeftButton:
            self.rubber.reset()
            return
        ori = self.get_orientation(mouseEvent.pos())
        if ori is None:
            self.rubber.reset()
            return
        dlg = OrientationDialog(ori, self.rubber)
        if dlg.exec_():
            if ori.length != 0:
                ori.save()
        self.rubber.reset()

    def get_orientation(self, pos):
        match = self.snap_to_segment(pos)
        if not match.hasEdge():
            return None
        vertices = match.edgePoints()
        po = match.point()
        dist = (po.sqrDist(vertices[0]), po.sqrDist(vertices[1]))
        mindist = min(dist)
        if mindist == 0:
            return None
        i = dist.index(mindist)
        ve = vertices[i]
        az = po.azimuth(ve)
        return Orientation(self.iface, ve, az)
