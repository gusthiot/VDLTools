# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2017-01-17
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

from PyQt4.QtGui import (QDialog,
                         QGridLayout,
                         QPushButton,
                         QLabel)
from PyQt4.QtCore import QCoreApplication


class ImportMeasuresDialog(QDialog):
    """
    Dialog class to confirm the import
    """

    def __init__(self, data):
        """
        Constructor
        """
        QDialog.__init__(self)
        self.__data = data
        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Delete Measures"))
        self.resize(300, 100)
        self.__layout = QGridLayout()

        self.__confirmLabel = QLabel(QCoreApplication.translate("VDLTools", "Do you want to remove these measures ?"))

        self.__layout.addWidget(self.__confirmLabel, 0, 0, 1, 2)

        pos = 1

        for data in self.__data:
            lineLabel = QLabel("id : " + str(data['id_survey']) + " - type : " + data['name_table'] + " - position : " + data['point'] + " - job : " + data['job'])
            self.__layout.addWidget(lineLabel, pos, 0, 1, 2)
            pos += 1

        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools", "Yes"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools", "No"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout.addWidget(self.__okButton, 1000, 0)
        self.__layout.addWidget(self.__cancelButton, 1000, 1)

        self.setLayout(self.__layout)

    def data(self):
        """
        To get the displayed data
        :return: displayed data
        """
        return self.__data

    def okButton(self):
        """
        To get the ok button instance
        :return: ok button instance
        """
        return self.__okButton

    def cancelButton(self):
        """
        To get the cancel button instance
        :return: cancel button instance
        """
        return self.__cancelButton
