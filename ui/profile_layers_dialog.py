# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-05-09
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
from future.builtins import range

from PyQt4.QtGui import (QDialog,
                         QGridLayout,
                         QPushButton,
                         QLabel,
                         QCheckBox)
from PyQt4.QtCore import QCoreApplication


class ProfileLayersDialog(QDialog):
    """
    Dialog class to add points layers to the profile
    """

    def __init__(self, pointLayers, with_mnt):
        """
        Constructor
        :param pointLayers: available points layers
        """
        QDialog.__init__(self)
        self.__pointLayers = pointLayers
        self.__with_mnt = with_mnt
        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Add Points Layers Profiles"))
        self.resize(300, 100)
        self.__layout = QGridLayout()
        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools", "OK"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools", "Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layersLabel = QLabel(QCoreApplication.translate("VDLTools", "Also points layers profile ? :"))
        self.__layersLabel.setMinimumHeight(20)
        self.__layersLabel.setMinimumWidth(50)

        self.__layout.addWidget(self.__layersLabel, 0, 0, 1, 4)

        self.__layLabels = []
        self.__layChecks = []

        for i in range(len(self.__pointLayers)):
            label = QLabel(self.__pointLayers[i].name() + " :")
            label.setMinimumHeight(20)
            label.setMinimumWidth(50)
            self.__layLabels.append(label)
            self.__layout.addWidget(self.__layLabels[i], i+1, 1)
            check = QCheckBox()
            check.setChecked(True)
            self.__layChecks.append(check)
            self.__layout.addWidget(self.__layChecks[i], i+1, 2)

        self.__mntLabels = []
        self.__mntChecks = []
        self.__mntTitles = ["MNT", "MNS", "Rocher"]

        if with_mnt:
            k = len(self.__pointLayers)
            for i in range(len(self.__mntTitles)):
                label = QLabel(self.__mntTitles[i] + " :")
                label.setMinimumHeight(20)
                label.setMinimumWidth(50)
                self.__mntLabels.append(label)
                self.__layout.addWidget(self.__mntLabels[i], i+k+1, 1)
                check = QCheckBox()
                check.setChecked(False)
                self.__mntChecks.append(check)
                self.__layout.addWidget(self.__mntChecks[i], i+k+1, 2)

        self.__layout.addWidget(self.__okButton, 100, 1)
        self.__layout.addWidget(self.__cancelButton, 100, 2)

        self.setLayout(self.__layout)

    def getUsedMnts(self):
        """
        To get the selected MN profiles
        :return: selected MN profiles
        """
        if self.__with_mnt:
            used = []
            for i in range(len(self.__mntChecks)):
                used.append(self.__mntChecks[i].isChecked())
            return used
        else:
            return None

    def getLayers(self):
        """
        To get the selected points layers
        :return: selected points layers
        """
        layers = []
        for i in range(len(self.__pointLayers)):
            if self.__layChecks[i].isChecked():
                layers.append(self.__pointLayers[i])
        return layers

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
