# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-09-26
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


from qgis.PyQt.QtWidgets import (QDialog,
                                 QGridLayout,
                                 QPushButton,
                                 QLabel)
from qgis.PyQt.QtCore import QCoreApplication


class FieldsSettingsDialog(QDialog):
    """
    Dialog class to parametrize the memory lines layer fields
    """

    def __init__(self):
        """
        Constructor
        """
        QDialog.__init__(self)
        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Memory lines layer fields"))

        self.resize(400, 200)
        self.__layout = QGridLayout()

        titleLabel = QLabel(QCoreApplication.translate("VDLTools", "One or more fields needed are missing in the memory lines layer."))
        titleLabel.setMinimumHeight(20)
        titleLabel.setMinimumWidth(50)
        self.__layout.addWidget(titleLabel, 0, 0)

        subtitleLabel = QLabel(QCoreApplication.translate("VDLTools", "You want to : "))
        subtitleLabel.setMinimumHeight(20)
        subtitleLabel.setMinimumWidth(50)
        self.__layout.addWidget(subtitleLabel, 1, 0)

        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools", "Add the needed fields in the layer and use it"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)
        self.__layout.addWidget(self.__okButton, 2, 0)

        self.__butButton = QPushButton(QCoreApplication.translate("VDLTools", "Use it without those fields"))
        self.__butButton.setMinimumHeight(20)
        self.__butButton.setMinimumWidth(100)
        self.__layout.addWidget(self.__butButton, 3, 0)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools", "Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)
        self.__layout.addWidget(self.__cancelButton, 4, 0)

        self.setLayout(self.__layout)

    def okButton(self):
        """
        To get the ok button instance
        :return: ok button instance
        """
        return self.__okButton

    def butButton(self):
        """
        To get the but button instance
        :return: but button instance
        """
        return self.__butButton

    def cancelButton(self):
        """
        To get the cancel button instance
        :return: cancel button instance
        """
        return self.__cancelButton
