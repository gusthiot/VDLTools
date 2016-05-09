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

from PyQt4.QtGui import (QDialog,
                         QGridLayout,
                         QPushButton,
                         QLabel,
                         QDateEdit,
                         QLineEdit,
                         QIntValidator,
                         QDoubleValidator)


class DuplicateAttributesDialog(QDialog):
    def __init__(self, fields, attributes):
        QDialog.__init__(self)
        self.__attributes = attributes
        self.__fields = fields
        self.setWindowTitle("Set attributes")
        self.resize(300, 100)
        self.__layout = QGridLayout()
        self.__okButton = QPushButton("OK")
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton("Cancel")
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__attLabels = []
        self.__attEdits = []

        for i in xrange(len(self.__attributes)):
            label = QLabel("label" + str(i))
            label.setText(fields[i].name() + " :")
            label.setMinimumHeight(20)
            label.setMinimumWidth(50)
            self.__attLabels.append(label)
            self.__layout.addWidget(self.__attLabels[i], i, 1)
            typeName = self.__fields[i].typeName()

            if typeName == "Date":
                if str(self.__attributes[i]) != "NULL":
                    edit = QDateEdit(self.__attributes[i])
                else:
                    edit = QDateEdit(None)
            else:
                edit = QLineEdit("line" + str(i))
                if str(self.__attributes[i]) != "NULL":
                    edit.setText(str(self.__attributes[i]))
                else:
                    edit.setText("")
                if typeName == "Integer" or typeName == "Integer64":
                    edit.setValidator(QIntValidator(-1000, 1000, self))
                elif typeName == "Real":
                    edit.setValidator(QDoubleValidator(-1000, 1000, 4, self))
            self.__attEdits.append(edit)
            self.__layout.addWidget(self.__attEdits[i], i, 2)

        self.__layout.addWidget(self.__okButton, 100, 1)
        self.__layout.addWidget(self.__cancelButton, 100, 2)
        self.setLayout(self.__layout)

    def okButton(self):
        return self.__okButton

    def cancelButton(self):
        return self.__cancelButton

    def getAttributes(self):
        for i in xrange(len(self.__attributes)):
            typeName = self.__fields[i].typeName()

            if typeName == "Date":
                if self.__attEdits[i] is not None:
                    self.__attributes[i] = self.__attEdits[i].date()
                else:
                    self.__attributes[i] = None
            elif typeName == "Integer" or typeName == "Integer64":
                if self.__attEdits[i].text() != "":
                    self.__attributes[i] = int(self.__attEdits[i].text())
                else:
                    self.__attributes[i] = None
            elif typeName == "Real":
                if self.__attEdits[i].text() != "":
                    self.__attributes[i] = float(self.__attEdits[i].text())
                else:
                    self.__attributes[i] = None
            else:
                self.__attributes[i] = self.__attEdits[i].text()
        return self.__attributes
