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
        self.__memoryPointsLayer = None
        self.__memoryLinesLayer = None
        self.__configTable = None

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
        self.__memoryLinesLayer = self.__showDlg.linesLayer()
        self.__memoryLinesLayer.layerDeleted.connect(self.__memoryLinesLayerDeleted)
        self.__memoryPointsLayer = self.__showDlg.pointsLayer()
        self.__memoryPointsLayer.layerDeleted.connect(self.__memoryPointsLayerDeleted)
        self.__configTable = self.__showDlg.configTable()

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

    def __memoryPointsLayerDeleted(self):
        """
        To delete the saved memory points layer
        """
        self.__memoryPointsLayer = None

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
        self.__memoryPointsLayer.layerDeleted.connect(self.__memoryPointsLayerDeleted)

    def setLinesLayer(self, linesLayer):
        """
        To set the saved memory lines layer
        :param linesLayer: memory lines layer to save
        """
        self.__memoryLinesLayer = linesLayer
        self.__memoryLinesLayer.layerDeleted.connect(self.__memoryLinesLayerDeleted)

    def setConfigTable(self, configTable):
        """
        To set the saved config table
        :param configTable: config table to save
        """
        self.__configTable = configTable
