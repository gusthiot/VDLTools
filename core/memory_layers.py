# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# Intersect It is a QGIS plugin to place observations (distance or orientation)
# with their corresponding precision, intersect them using a least-squares solution
# and save dimensions in a dedicated layer to produce maps.
#
# Copyright    : (C) 2013 Denis Rouzaud
# Email        : denis.rouzaud@gmail.com
#
# -----------------------------------------------------------
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
# with this progsram; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# ---------------------------------------------------------------------
"""
Reimplemented for QGIS3 by :
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2020-08-11
        git sha              : $Format:%H$
        copyright            : (C) 2020 Ville de Lausanne
        author               : Christophe Gusthiot
        email                : i2g@gusthiot.ch
 ***************************************************************************/
"""

from qgis.core import (QgsProject,
                       QgsVectorLayer)


class MemoryLayers(object):
    """
    Class for memory layers creation
    """

    def __init__(self, iface, settings):
        """
        Constructor
        :param iface: interface
        .:param settings: settings containing layers
        """
        self.__iface = iface
        self.__settings = settings
        self.__lineLayerID = None
        self.__pointLayerID = None

    def lineLayer(self):
        """
        To get the line layer
        :return: a line layer
        """
        if self.__settings is not None:
            if self.__settings.linesLayer is not None:
                layer = self.__settings.linesLayer
                self.__lineLayerID = layer.id()
                return layer
        layer = QgsProject.instance().mapLayer(self.__lineLayerID)
        if layer is None:
            epsg = self.__iface.mapCanvas().mapSettings().destinationCrs().authid()
            layer = QgsVectorLayer(
                "LineString?crs=%s&index=yes&field=id:string&field=type:string&field=mesure:double&field=x:double&field=y:double"
                                   % epsg, "Memory Lines", "memory")
            QgsProject.instance().addMapLayer(layer)
            layer.destroyed.connect(self.__lineLayerDeleted)
            self.__lineLayerID = layer.id()
            if self.__settings is not None:
                self.__settings.linesLayer = layer
        else:
            self.__iface.legendInterface().setLayerVisible(layer, True)
        return layer

    def __lineLayerDeleted(self):
        """
        To deselect the line layer when it is deleted
        """
        self.lineLayerID = None

    def pointLayer(self):
        """
        To get the point layer
        :return: a point layer
        """
        if self.__settings is not None:
            if self.__settings.pointsLayer is not None:
                layer = self.__settings.pointsLayer
                self.__pointLayerID = layer.id()
                return layer
        layer = QgsProject.instance().mapLayer(self.__pointLayerID)
        if layer is None:
            epsg = self.__iface.mapCanvas().mapSettings().destinationCrs().authid()
            layer = QgsVectorLayer("Point?crs=%s&index=yes&field=id:string" % epsg, "Memory Points", "memory")
            QgsProject.instance().addMapLayer(layer)
            layer.destroyed.connect(self.__pointLayerDeleted)
            self.__pointLayerID = layer.id()
            if self.__settings is not None:
                self.__settings.pointsLayer = layer
        else:
            self.__iface.legendInterface().setLayerVisible(layer, True)
        return layer

    def __pointLayerDeleted(self):
        """
        To deselect the point layer when it is deleted
        """
        self.__pointLayerID = None
