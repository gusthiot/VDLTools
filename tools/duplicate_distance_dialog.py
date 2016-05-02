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
        self.distanceLabel = QLabel("distance :")
        self.distanceLabel.setMinimumHeight(20)
        self.distanceLabel.setMinimumWidth(50)

        self.distanceEdit = QLineEdit("inputMask")
        self.distanceEdit.setMinimumHeight(20)
        self.distanceEdit.setMinimumWidth(120)
        self.distanceEdit.setValidator(QDoubleValidator(-1000, 1000, 4, self))

        self.previewButton = QPushButton("Preview")
        self.previewButton.setMinimumHeight(20)
        self.previewButton.setMinimumWidth(100)

        self.okButton = QPushButton("OK")
        self.okButton.setMinimumHeight(20)
        self.okButton.setMinimumWidth(100)

        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.setMinimumHeight(20)
        self.cancelButton.setMinimumWidth(100)

        self.layout = QGridLayout()
        self.layout.addWidget(self.distanceLabel, 0, 0)
        self.layout.addWidget(self.distanceEdit, 0, 1)

        if isComplexPolygon:
            self.polygonLabel = QLabel("In which direction the internal part has to be duplicated ?")
            self.polygonLabel.setMinimumHeight(20)
            self.polygonLabel.setMinimumWidth(50)
            self.layout.addWidget(self.polygonLabel, 1, 0, 1, 3)

            self.directions = [QRadioButton("same"), QRadioButton("opposite")]
            self.directions[0].setChecked(True)
            self.direction_button_group = QButtonGroup()
            for i in xrange(len(self.directions)):
                self.layout.addWidget(self.directions[i], 2, i+1)
                self.direction_button_group.addButton(self.directions[i], i)

        self.layout.addWidget(self.previewButton, 3, 0)
        self.layout.addWidget(self.okButton, 3, 1)
        self.layout.addWidget(self.cancelButton, 3, 2)
        self.setLayout(self.layout)
