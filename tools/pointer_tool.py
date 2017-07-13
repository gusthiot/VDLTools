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
from qgis.core import (QgsWKBTypes,
                       QgsMapLayer,
                       QgsSnappingUtils,
                       QgsTolerance,
                       QgsPointLocator,
                       QGis)
from qgis.gui import (QgsMapTool,
                      QgsMessageBar)
from PyQt4.QtCore import (Qt,
                          QCoreApplication)
from PyQt4.QtGui import QMessageBox
from ..core.finder import Finder


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
        types = [QgsWKBTypes.PointZ, QgsWKBTypes.LineStringZ, QgsWKBTypes.CircularStringZ, QgsWKBTypes.CompoundCurveZ,
                 QgsWKBTypes.CurvePolygonZ, QgsWKBTypes.PolygonZ]
        display = ""
        for layer in self.canvas().layers():
            if layer.type() == QgsMapLayer.VectorLayer and QGis.fromOldWkbType(layer.wkbType()) in types:
                layerConfig = QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Vertex, 10, QgsTolerance.Pixels)
                features = Finder.findFeaturesAt(event.mapPoint(), layerConfig, self)
                if len(features) > 0:
                    display += layer.name() + " : \n"
                    for f in features:
                        if f.geometry().type() == QGis.Point:
                            alt = f.geometry().geometry().z()
                        elif f.geometry().type() == QGis.Line:
                            closest = f.geometry().closestVertex(event.mapPoint())
                            alt = f.geometry().geometry().zAt(closest[1])
                        elif f.geometry().type() == QGis.Polygon:
                            self.__iface.messageBar().pushMessage(
                                QCoreApplication.translate("VDLTools", "Polygon not yet implemented"),
                                level=QgsMessageBar.WARNING)
                            continue
                        else:
                            continue
                        display += "    " + str(f.id()) + " | " + str(alt) + " m.\n"
        if display != "":
            QMessageBox.information(None, QCoreApplication.translate("VDLTools", "Id | Elevation"), display)
