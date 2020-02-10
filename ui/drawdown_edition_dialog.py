# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2018-11-07
        git sha              : $Format:%H$
        copyright            : (C) 2018 Ville de Lausanne
        author               : Ingénierie Informatique Gusthiot, Christophe Gusthiot
        email                : i2g@gusthiot.ch
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


class DrawdownEditionDialog(QDialog):
    """
    Dialog class to display the layers to be edited
    """

    def __init__(self, layers):
        """
        Constructor
        """
        QDialog.__init__(self)
        self.__layers = layers
        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Edition Confirmation"))
        self.__layout = QGridLayout()

        titleLabel = QLabel(QCoreApplication.translate("VDLTools", "Do you really want to edit these layers ?"))
        self.__layout.addWidget(titleLabel, 0, 0, 1, 2)

        pos = 1
        for layer in self.__layers:
            label = QLabel(" - " + layer.name())
            self.__layout.addWidget(label, pos, 0, 1, 2)
            pos += 1

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools", "Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        pos = len(self.__layers) + 1
        self.__layout.addWidget(self.__cancelButton, pos, 0)

        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools", "OK"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)
        self.__layout.addWidget(self.__okButton, pos, 1)


        self.setLayout(self.__layout)

    def getLayers(self):
        """
        To get layers to be edited
        :return: layers list
        """
        return self.__layers

    def cancelButton(self):
        """
        To get the cancel button instance
        :return: cancel button instance
        """
        return self.__cancelButton

    def okButton(self):
        """
        To get the ok button instance
        :return: ok button instance
        """
        return self.__okButton
