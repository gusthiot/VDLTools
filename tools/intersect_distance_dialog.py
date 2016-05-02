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

from PyQt4.QtGui import QDialog, QGridLayout, QPushButton, QLabel, QLineEdit, QDoubleSpinBox


class IntersectDistanceDialog(QDialog):
    def __init__(self, mapPoint):
        QDialog.__init__(self)
        self.mapPoint = mapPoint
        self.setWindowTitle("Place distance")
        self.resize(275, 177)
        self.gridLayout = QGridLayout()

        self.label = QLabel("Distance")
        self.gridLayout.addWidget(self.label, 2, 1, 1, 1)

        self.observation = QDoubleSpinBox()
        self.observation.setDecimals(4)
        self.observation.setMaximum(999999.99)
        self.observation.setSingleStep(1.0)
        self.gridLayout.addWidget(self.observation, 2, 2, 1, 1)

        self.label_3 = QLabel("m")
        self.gridLayout.addWidget(self.label_3, 2, 3, 1, 1)

        self.okButton = QPushButton("OK")
        self.okButton.setMinimumHeight(20)
        self.okButton.setMinimumWidth(100)

        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.setMinimumHeight(20)
        self.cancelButton.setMinimumWidth(100)

        self.gridLayout.addWidget(self.okButton, 5, 1)
        self.gridLayout.addWidget(self.cancelButton, 5, 2)

        self.label_5 = QLabel("y")
        self.gridLayout.addWidget(self.label_5, 1, 1, 1, 1)

        self.label_6 = QLabel("x")
        self.gridLayout.addWidget(self.label_6, 0, 1, 1, 1)

        self.x = QLineEdit("x")
        self.x.setText(str(self.mapPoint.x()))
        self.x.setEnabled(False)
        self.gridLayout.addWidget(self.x, 0, 2, 1, 2)

        self.y = QLineEdit("y")
        self.y.setText(str(self.mapPoint.y()))
        self.y.setEnabled(False)
        self.gridLayout.addWidget(self.y, 1, 2, 1, 2)

        self.setLayout(self.gridLayout)

