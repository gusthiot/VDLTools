# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2019-06-18
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


class ProfileForceDialog(QDialog):
    """
    Dialog class to confirm the extrapolation
    """

    def __init__(self, message):
        """
        Constructor
        :param message: label for dialog
        """
        QDialog.__init__(self)
        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Edition Confirmation"))
        self.resize(300, 100)
        self.__layout = QGridLayout()

        self.__confirmLabel = QLabel(message)

        self.__layout.addWidget(self.__confirmLabel, 0, 0, 1, 2)

        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools", "Yes"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(300)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools", "No"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout.addWidget(self.__okButton, 1, 0)
        self.__layout.addWidget(self.__cancelButton, 1, 1)

        self.setLayout(self.__layout)

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
