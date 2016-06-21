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


class ShowSettings:

    def __init__(self, iface):
        self.__iface = iface
        self.__icon_path = None
        self.__text = 'Settings'
        self.__showDlg = None
        self.__memoryPointsLayer = None
        self.__memoryLinesLayer = None

    def icon_path(self):
        return self.__icon_path

    def text(self):
        return self.__text

    def start(self):
        self.__showDlg = ShowSettingsDialog(self.__iface, self.__memoryPointsLayer, self.__memoryLinesLayer)
        self.__showDlg.okButton().clicked.connect(self.__onOk)
        self.__showDlg.cancelButton().clicked.connect(self.__onCancel)
        self.__showDlg.show()

    def __onOk(self):
        self.__showDlg.close()
        self.__showDlg.okButton().clicked.disconnect(self.__onOk)
        self.__showDlg.cancelButton().clicked.disconnect(self.__onCancel)
        self.__memoryLinesLayer = self.__showDlg.linesLayer()
        self.__memoryPointsLayer = self.__showDlg.pointsLayer()

    def __onCancel(self):
        self.__showDlg.close()
        self.__showDlg.okButton().clicked.disconnect(self.__onOk)
        self.__showDlg.cancelButton().clicked.disconnect(self.__onCancel)

    def pointsLayer(self):
        return self.__memoryPointsLayer

    def linesLayer(self):
        return self.__memoryLinesLayer

    def setPointsLayer(self, pointsLayer):
        self.__memoryPointsLayer = pointsLayer

    def setLinesLayer(self, linesLayer):
        self.__memoryLinesLayer = linesLayer
