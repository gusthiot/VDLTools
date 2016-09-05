# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-06-20
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

from ..ui.show_settings_dialog import ShowSettingsDialog
from PyQt4.QtCore import QCoreApplication
from qgis.core import (QgsProject,
                       QGis,
                       QgsMapLayer)

class ShowSettings:

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        self.__iface = iface
        self.__icon_path = ':/plugins/VDLTools/icons/settings_icon.png'
        self.__text = QCoreApplication.translate("VDLTools","Settings")
        self.__showDlg = None
        self.__configTable = None
        self.__memoryPointsLayer = None
        self.__memoryLinesLayer = None
        self.__project_loaded()
        QgsProject.instance().readProject.connect(self.__project_loaded)

    def __project_loaded(self):
        self.__configTable = QgsProject.instance().readEntry("VDLTools", "config_table", None)[0]
        mpl_id = QgsProject.instance().readEntry("VDLTools", "memory_points_layer", None)[0]
        mll_id = QgsProject.instance().readEntry("VDLTools", "memory_lines_layer", None)[0]
        if mpl_id != -1 or mll_id != -1:
            for layer in self.__iface.mapCanvas().layers():
                if layer is not None \
                    and layer.type() == QgsMapLayer.VectorLayer \
                        and layer.providerType() == "memory":
                    if layer.geometryType() == QGis.Point:
                        if layer.id() == mpl_id:
                            self.__memoryPointsLayer = layer
                    if layer.geometryType() == QGis.Line:
                        if layer.id() == mll_id:
                            self.__memoryLinesLayer = layer

    def icon_path(self):
        """
        To get the icon path
        :return: icon path
        """
        return self.__icon_path

    def text(self):
        """
        To get the menu text
        :return: menu text
        """
        return self.__text

    def start(self):
        """
        To start the show settings, meaning display a Show Settings Dialog
        """
        self.__showDlg = ShowSettingsDialog(self.__iface, self.__memoryPointsLayer, self.__memoryLinesLayer,
                                            self.__configTable)
        self.__showDlg.okButton().clicked.connect(self.__onOk)
        self.__showDlg.cancelButton().clicked.connect(self.__onCancel)
        self.__showDlg.show()

    def __onOk(self):
        """
        When the Ok button in Show Settings Dialog is pushed
        """
        self.__showDlg.close()
        self.setLinesLayer(self.__showDlg.linesLayer())
        self.setPointsLayer(self.__showDlg.pointsLayer())
        self.setConfigTable(self.__showDlg.configTable())

    def __onCancel(self):
        """
        When the Cancel button in Show Settings Dialog is pushed
        """
        self.__showDlg.close()

    def __memoryLinesLayerDeleted(self):
        """
        To delete the saved memory lines layer
        """
        self.__memoryLinesLayer = None
        QgsProject.instance().writeEntry("VDLTools", "memory_lines_layer", None)

    def __memoryPointsLayerDeleted(self):
        """
        To delete the saved memory points layer
        """
        self.__memoryPointsLayer = None
        QgsProject.instance().writeEntry("VDLTools", "memory_points_layer", None)

    def pointsLayer(self):
        """
        To get the saved memory points layer
        :return: saved memory points layer
        """
        return self.__memoryPointsLayer

    def linesLayer(self):
        """
        To get the saved memory lines layer
        :return: saved memory lines layer
        """
        return self.__memoryLinesLayer

    def configTable(self):
        """
        To get the saved config table (for import tool)
        :return: saved config table
        """
        return self.__configTable

    def setPointsLayer(self, pointsLayer):
        """
        To set the saved memory points layer
        :param pointsLayer: memory points layer to save
        """
        self.__memoryPointsLayer = pointsLayer
        id = None
        if pointsLayer is not None:
            id = pointsLayer.id()
            self.__memoryPointsLayer.layerDeleted.connect(self.__memoryPointsLayerDeleted)
        QgsProject.instance().writeEntry("VDLTools", "memory_points_layer", id)

    def setLinesLayer(self, linesLayer):
        """
        To set the saved memory lines layer
        :param linesLayer: memory lines layer to save
        """
        self.__memoryLinesLayer = linesLayer
        id = None
        if linesLayer is not None:
            id = linesLayer.id()
            self.__memoryLinesLayer.layerDeleted.connect(self.__memoryLinesLayerDeleted)
        QgsProject.instance().writeEntry("VDLTools", "memory_lines_layer", id)

    def setConfigTable(self, configTable):
        """
        To set the saved config table
        :param configTable: config table to save
        """
        self.__configTable = configTable
        QgsProject.instance().writeEntry("VDLTools", "config_table", configTable)
