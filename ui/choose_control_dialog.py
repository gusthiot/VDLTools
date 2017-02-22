# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2017-02-14
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
                         QButtonGroup,
                         QCheckBox,
                         QGridLayout,
                         QPushButton,
                         QLabel)
from PyQt4.QtCore import QCoreApplication


class ChooseControlDialog(QDialog):
    """
    Dialog class to choose the controls to process
    """

    def __init__(self, names):
        """
        Constructor
        """
        QDialog.__init__(self)
        self.__names = names
        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Choose Controls"))
        self.resize(300, 100)
        self.__layout = QGridLayout()

        self.__confirmLabel = QLabel(
            QCoreApplication.translate("VDLTools",
                                       "Choose which controls you want to process :"))

        self.__layout.addWidget(self.__confirmLabel, 0, 0, 1, 2)

        self.__group = QButtonGroup()

        self.__controlsLabels = []
        self.__controlsChecks = []

        for i in range(len(self.__names)):
            label = QLabel(self.__names[i])
            label.setMinimumHeight(20)
            label.setMinimumWidth(50)
            self.__controlsLabels.append(label)
            self.__layout.addWidget(self.__controlsLabels[i], i+1, 0)
            check = QCheckBox()
            check.setChecked(False)
            self.__controlsChecks.append(check)
            self.__layout.addWidget(self.__controlsChecks[i], i+1, 1)

        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools","Ok"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools","Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout.addWidget(self.__okButton, 100, 0)
        self.__layout.addWidget(self.__cancelButton, 100, 1)

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

    def controls(self):
        """
        To get the selected controls
        :return: control list
        """
        controls = []
        for i in range(len(self.__names)):
            if self.__controlsChecks[i].isChecked():
                controls.append(self.__names[i])
        return controls
