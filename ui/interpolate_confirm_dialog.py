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

from PyQt4.QtGui import (QDialog,
                         QGridLayout,
                         QPushButton,
                         QLabel)
from PyQt4.QtCore import QCoreApplication


class InterpolateConfirmDialog(QDialog):

    def __init__(self):
        """
        Constructor
        """
        QDialog.__init__(self)
        self.setWindowTitle(QCoreApplication.translate("VDLTools","Edition Confirmation"))
        self.resize(300, 100)
        self.__layout = QGridLayout()

        self.__confirmLabel = QLabel(
            QCoreApplication.translate("VDLTools","This LineString layer is not editable, what do you want to do ?"))

        self.__layout.addWidget(self.__confirmLabel, 0, 0, 1, 3)

        self.__allButton = QPushButton(
            QCoreApplication.translate("VDLTools","Create point, and edit line with new vertex"))
        self.__allButton.setMinimumHeight(20)
        self.__allButton.setMinimumWidth(300)

        self.__ptButton = QPushButton(QCoreApplication.translate("VDLTools","Create only the point"))
        self.__ptButton.setMinimumHeight(20)
        self.__ptButton.setMinimumWidth(200)

        self.__vtButton = QPushButton(QCoreApplication.translate("VDLTools","Just edit line with new vertex"))
        self.__vtButton.setMinimumHeight(20)
        self.__vtButton.setMinimumWidth(200)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools","Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout.addWidget(self.__allButton, 1, 1)
        self.__layout.addWidget(self.__ptButton, 1, 2)
        self.__layout.addWidget(self.__vtButton, 1, 3)
        self.__layout.addWidget(self.__cancelButton, 1, 4)

        self.setLayout(self.__layout)

    def setMainLabel(self, label):
        """
        To set the title
        :param label: title
        """
        self.__confirmLabel.setText(label)

    def setAllLabel(self, label):
        """
        To set the all button title
        :param label: title
        """
        self.__allButton.setText(label)

    def setVtLabel(self, label):
        """
        To set the vertex button title
        :param label: title
        """
        self.__vtButton.setText(label)

    def allButton(self):
        """
        To get the all button instance
        :return: all button instance
        """
        return self.__allButton

    def ptButton(self):
        """
        To get the point button instance
        :return: point button instance
        """
        return self.__ptButton

    def cancelButton(self):
        """
        To get the cancel button instance
        :return: cancel button instance
        """
        return self.__cancelButton

    def vtButton(self):
        """
        To get the vertex button instance
        :return: vertex button instance
        """
        return self.__vtButton
