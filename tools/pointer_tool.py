# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2017-01-23
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
from builtins import str
from qgis.core import (QgsWkbTypes,
                       Qgis,
                       QgsMapLayer,
                       QgsTolerance)
from qgis.gui import QgsMapTool
from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt.QtWidgets import QMessageBox
from ..core.finder import Finder
from ..core.geometry_v2 import GeometryV2


class PointerTool(QgsMapTool):
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
        self.icon_path = ':/plugins/VDLTools/icons/pointer_icon.png'
        self.text = QCoreApplication.translate("VDLTools", "Elevation pointer")
        self.setCursor(Qt.ArrowCursor)

    def setTool(self):
        """
        To set the current tool as this one
        """
        self.canvas().setMapTool(self)

    def canvasReleaseEvent(self, event):
        """
        When the mouse is clicked
        :param event: mouse event
        """
        types = [QgsWkbTypes.PointZ, QgsWkbTypes.LineStringZ, QgsWkbTypes.CircularStringZ, QgsWkbTypes.CompoundCurveZ,
                 QgsWkbTypes.CurvePolygonZ, QgsWkbTypes.PolygonZ]
        display = ""
        for layer in self.canvas().layers():
            if layer.type() == QgsMapLayer.VectorLayer and GeometryV2.getAdaptedWKB(layer.wkbType()) in types:
                features = Finder.findFeaturesAt(event.mapPoint(), layer, 10, QgsTolerance.Pixels, self)
                if len(features) > 0:
                    display += layer.name() + " : \n"
                    for f in features:
                        geom = f.geometry()
                        if geom.type() == QgsWkbTypes.PointGeometry:
                            alt = geom.get().z()
                        elif geom.type() == QgsWkbTypes.LineGeometry:
                            closest = geom.closestVertex(event.mapPoint())
                            line = geom.get()
                            alt = line.zAt(closest[1])
                        elif geom.type() == QgsWkbTypes.PolygonGeometry:
                            self.__iface.messageBar().pushMessage(
                                QCoreApplication.translate("VDLTools", "Polygon not yet implemented"),
                                level=Qgis.Warning)
                            continue
                        else:
                            continue
                        display += "    " + str(f.id()) + " | " + str(alt) + " m.\n"
        if display != "":
            QMessageBox.information(None, QCoreApplication.translate("VDLTools", "Id | Elevation"), display)
