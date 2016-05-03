# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-04-05
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

from PyQt4.QtGui import QDialog, QGridLayout, QPushButton, QLabel
from PyQt4.QtGui import QLineEdit, QDoubleValidator, QRadioButton, QButtonGroup


class DuplicateDistanceDialog(QDialog):
    def __init__(self, isComplexPolygon):
        QDialog.__init__(self)
        self.setWindowTitle("Duplicate")
        self.resize(300, 100)
        self.__distanceLabel = QLabel("distance :")
        self.__distanceLabel.setMinimumHeight(20)
        self.__distanceLabel.setMinimumWidth(50)

        self.__distanceEdit = QLineEdit("inputMask")
        self.__distanceEdit.setMinimumHeight(20)
        self.__distanceEdit.setMinimumWidth(120)
        self.__distanceEdit.setValidator(QDoubleValidator(-1000, 1000, 4, self))

        self.__previewButton = QPushButton("Preview")
        self.__previewButton.setMinimumHeight(20)
        self.__previewButton.setMinimumWidth(100)

        self.__okButton = QPushButton("OK")
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton("Cancel")
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout = QGridLayout()
        self.__layout.addWidget(self.__distanceLabel, 0, 0)
        self.__layout.addWidget(self.__distanceEdit, 0, 1)

        if isComplexPolygon:
            self.__polygonLabel = QLabel("In which direction the internal part has to be duplicated ?")
            self.__polygonLabel.setMinimumHeight(20)
            self.__polygonLabel.setMinimumWidth(50)
            self.__layout.addWidget(self.__polygonLabel, 1, 0, 1, 3)

            self.__directions = [QRadioButton("same"), QRadioButton("opposite")]
            self.__directions[0].setChecked(True)
            self.__direction_button_group = QButtonGroup()
            for i in xrange(len(self.__directions)):
                self.__layout.addWidget(self.__directions[i], 2, i+1)
                self.__direction_button_group.addButton(self.__directions[i], i)

        self.__layout.addWidget(self.__previewButton, 3, 0)
        self.__layout.addWidget(self.__okButton, 3, 1)
        self.__layout.addWidget(self.__cancelButton, 3, 2)
        self.setLayout(self.__layout)

    def previewButton(self):
        return self.__previewButton

    def okButton(self):
        return self.__okButton

    def cancelButton(self):
        return self.__cancelButton

    def distanceEditText(self):
        return self.__distanceEdit.text()

    def setDistanceEditText(self, text):
        self.__distanceEdit.setText(text)

    def isInverted(self):
        return self.__direction_button_group.checkedId() == 1
