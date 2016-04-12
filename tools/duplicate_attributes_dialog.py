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

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class DuplicateAttributesDialog(QDialog):
    def __init__(self, fields, attributes):
        QDialog.__init__(self)
        self.attributes = attributes
        self.fields = fields
        self.setWindowTitle("Set attributes")
        self.resize(300, 100)
        self.layout = QGridLayout()
        self.okButton = QPushButton("OK")
        self.okButton.setMinimumHeight(20)
        self.okButton.setMinimumWidth(100)

        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.setMinimumHeight(20)
        self.cancelButton.setMinimumWidth(100)

        self.attLabels = []
        self.attEdits = []

        for i in xrange(len(attributes)):
            label = QLabel("label" + str(i))
            label.setText(fields[i].name() + " :")
            label.setMinimumHeight(20)
            label.setMinimumWidth(50)
            self.attLabels.append(label)
            self.layout.addWidget(self.attLabels[i], i, 1)
            typeName = self.fields[i].typeName()

            if typeName == "Date":
                edit = QDateEdit(attributes[i])
            else:
                edit = QLineEdit("line" + str(i))
                edit.setText(str(attributes[i]))
                if typeName == "Integer" or typeName == "Integer64":
                    edit.setValidator(QIntValidator(-1000, 1000, self))
                elif typeName == "Real":
                    edit.setValidator(QDoubleValidator(-1000, 1000, 4, self))
            self.attEdits.append(edit)
            self.layout.addWidget(self.attEdits[i], i, 2)

        self.layout.addWidget(self.okButton, 100, 1)
        self.layout.addWidget(self.cancelButton, 100, 2)
        self.setLayout(self.layout)

    def getAttributes(self):
        for i in xrange(len(self.attributes)):
            typeName = self.fields[i].typeName()
            if typeName == "Date":
                self.attributes[i] = self.attEdits[i].date()
            elif typeName == "Integer" or typeName == "Integer64":
                self.attributes[i] = int(self.attEdits[i].text())
            elif typeName == "Real":
                self.attributes[i] = float(self.attEdits[i].text())
            else:
                self.attributes[i] = self.attEdits[i].text()
        return self.attributes


