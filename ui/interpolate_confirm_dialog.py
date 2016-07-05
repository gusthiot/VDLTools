# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-06-13
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

from PyQt4.QtGui import (QDialog, QGridLayout, QPushButton, QLabel)


class InterpolateConfirmDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setWindowTitle("Edition Confirmation")
        self.resize(300, 100)
        self.__layout = QGridLayout()

        self.__confirmLabel = QLabel("This LineString layer is not editable, what do you want to do ?")

        self.__layout.addWidget(self.__confirmLabel, 0, 0, 1, 3)

        self.__allButton = QPushButton("Create point, and edit line with new vertex")
        self.__allButton.setMinimumHeight(20)
        self.__allButton.setMinimumWidth(300)

        self.__ptButton = QPushButton("Create only the point")
        self.__ptButton.setMinimumHeight(20)
        self.__ptButton.setMinimumWidth(200)

        self.__vtButton = QPushButton("Just edit line with new vertex")
        self.__vtButton.setMinimumHeight(20)
        self.__vtButton.setMinimumWidth(200)

        self.__cancelButton = QPushButton("Cancel")
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout.addWidget(self.__allButton, 1, 1)
        self.__layout.addWidget(self.__ptButton, 1, 2)
        self.__layout.addWidget(self.__vtButton, 1, 3)
        self.__layout.addWidget(self.__cancelButton, 1, 4)

        self.setLayout(self.__layout)

    def setMainLabel(self, label):
        self.__confirmLabel.setText(label)

    def setAllLabel(self, label):
        self.__allButton.setText(label)

    def setVtLabel(self, label):
        self.__vtButton.setText(label)

    def allButton(self):
        return self.__allButton

    def ptButton(self):
        return self.__ptButton

    def cancelButton(self):
        return self.__cancelButton

    def vtButton(self):
        return self.__vtButton
