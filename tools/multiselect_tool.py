# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2017-01-31
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
from qgis.core import (QGis,
                       QgsWKBTypes,
                       QgsRectangle,
                       QgsMapLayer)
from area_tool import AreaTool


class MultiselectTool(AreaTool):
    """
    Map tool class to select object from multiple layers
    """

    selectedSignal = pyqtSignal()

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        AreaTool.__init__(self, iface)
        self.types = [QgsWKBTypes.PointZ, QgsWKBTypes.LineStringZ, QgsWKBTypes.CircularStringZ,
                      QgsWKBTypes.CompoundCurveZ, QgsWKBTypes.CurvePolygonZ, QgsWKBTypes.PolygonZ]
        self.releasedSignal.connect(self.__select)

    def __select(self):
        searchRect = QgsRectangle(self.first(), self.last())
        for layer in self.canvas().layers():
            if layer.type() == QgsMapLayer.VectorLayer and QGis.fromOldWkbType(layer.wkbType()) in self.types:
                layer.select(searchRect, False)
        self.selectedSignal.emit()
