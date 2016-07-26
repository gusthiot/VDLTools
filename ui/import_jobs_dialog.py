# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-07-26
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
                         QComboBox)


class ImportJobsDialog(QDialog):
    def __init__(self, jobs):
        QDialog.__init__(self)
        self.__jobs = jobs
        self.setWindowTitle("Choose job")
        self.resize(300, 100)
        self.__layout = QGridLayout()
        self.__okButton = QPushButton("OK")
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton("Cancel")
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout.addWidget(self.__okButton, 100, 1)
        self.__layout.addWidget(self.__cancelButton, 100, 2)

        label = QLabel("Job : ")
        label.setMinimumHeight(20)
        label.setMinimumWidth(50)
        self.__layout.addWidget(label, 0, 1)

        self.__jobCombo = QComboBox()
        self.__jobCombo.setMinimumHeight(20)
        self.__jobCombo.setMinimumWidth(50)
        self.__jobCombo.addItem("")
        for job in self.__jobs:
            self.__jobCombo.addItem(job)
        self.__layout.addWidget(self.__jobCombo, 0, 2)
        self.__jobCombo.currentIndexChanged.connect(self.__jobComboChanged)

        self.setLayout(self.__layout)

    def __jobComboChanged(self):
        if self.__pointCombo.itemText(0) == "":
            self.__pointCombo.removeItem(0)

    def okButton(self):
        return self.__okButton

    def cancelButton(self):
        return self.__cancelButton

    def job(self):
        index = self.__jobCombo.currentIndex()
        if self.__jobCombo.itemText(index) == "":
            return None
        else:
            return self.__jobs[index]
