# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-07-13
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


class MoveConfirmDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setWindowTitle("Move/Copy Confirmation")
        self.resize(300, 100)
        self.__layout = QGridLayout()

        self.__confirmLabel = QLabel("Would you like to move or to copy this feature ?")

        self.__layout.addWidget(self.__confirmLabel, 0, 0, 1, 3)

        self.__moveButton = QPushButton("Move")
        self.__moveButton.setMinimumHeight(20)
        self.__moveButton.setMinimumWidth(300)

        self.__copyButton = QPushButton("Copy")
        self.__copyButton.setMinimumHeight(20)
        self.__copyButton.setMinimumWidth(200)

        self.__cancelButton = QPushButton("Cancel")
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(200)

        self.__layout.addWidget(self.__moveButton, 1, 1)
        self.__layout.addWidget(self.__copyButton, 1, 2)
        self.__layout.addWidget(self.__cancelButton, 1, 3)

        self.setLayout(self.__layout)

    def moveButton(self):
        return self.__moveButton

    def copyButton(self):
        return self.__copyButton

    def cancelButton(self):
        return self.__cancelButton
