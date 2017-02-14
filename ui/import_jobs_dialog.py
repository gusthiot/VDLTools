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
                         QRadioButton,
                         QButtonGroup,
                         QCheckBox)
from PyQt4.QtCore import QCoreApplication


class ImportJobsDialog(QDialog):
    """
    Dialog class to choose the imported job
    """

    def __init__(self, jobs, selected):
        """
        Constructor
        :param jobs: all the jobs available for import
        """
        QDialog.__init__(self)
        self.__jobs = jobs
        self.__selected = selected
        self.setWindowTitle(QCoreApplication.translate("VDLTools","What to process"))
        self.resize(300, 100)
        self.__layout = QGridLayout()
        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools","OK"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools","Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout.addWidget(self.__okButton, 100, 1)
        self.__layout.addWidget(self.__cancelButton, 100, 2)

        self.__group = QButtonGroup()

        self.__jobButton = None
        if len(self.__jobs) > 0:
            self.__jobButton = QRadioButton(QCoreApplication.translate("VDLTools","Job(s)"))
            self.__layout.addWidget(self.__jobButton, 0, 1)
            self.__group.addButton(self.__jobButton)
            self.__jobButton.setChecked(True)

        self.__jobsLabels = []
        self.__jobsChecks = []

        for i in range(len(self.__jobs)):
            label = QLabel(self.__jobs[i])
            label.setMinimumHeight(20)
            label.setMinimumWidth(50)
            self.__jobsLabels.append(label)
            self.__layout.addWidget(self.__jobsLabels[i], i+1, 1)
            check = QCheckBox()
            check.setChecked(False)
            self.__jobsChecks.append(check)
            self.__layout.addWidget(self.__jobsChecks[i], i+1, 2)

        self.__pointsButton = None
        if self.__selected:
            self.__pointsButton = QRadioButton(QCoreApplication.translate("VDLTools","Selected Point(s)"))
            self.__layout.addWidget(self.__pointsButton, len(self.__jobs)+2, 1)
            self.__group.addButton(self.__pointsButton)
            if len(self.__jobs) == 0:
                self.__pointsButton.setChecked(True)

        self.setLayout(self.__layout)

    def okButton(self):
        """
        To get the ok button instance
        :return: ok button instance
        """
        return self.__okButton

    def jobsRadio(self):
        return self.__jobButton

    def pointsRadio(self):
        return self.__pointsButton

    def enableJobs(self, enable):
        for i in range(len(self.__jobs)):
            if enable:
                label = QLabel(self.__jobs[i])
                label.setMinimumHeight(20)
                label.setMinimumWidth(50)
                self.__jobsLabels[i] = label
                self.__layout.addWidget(self.__jobsLabels[i], i + 1, 1)
                check = QCheckBox()
                check.setChecked(False)
                self.__jobsChecks[i] = check
                self.__layout.addWidget(self.__jobsChecks[i], i+1, 2)
            else:
                self.__layout.removeWidget(self.__jobsLabels[i])
                self.__jobsLabels[i].deleteLater()
                self.__jobsLabels[i] = None
                self.__layout.removeWidget(self.__jobsChecks[i])
                self.__jobsChecks[i].deleteLater()
                self.__jobsChecks[i] = None



    def cancelButton(self):
        """
        To get the cancel button instance
        :return: cancel button instance
        """
        return self.__cancelButton

    def jobs(self):
        """
        To get the selected jobs
        :return: selected jobs
        """
        jobs = []
        for i in range(len(self.__jobs)):
            if self.__jobsChecks[i].isChecked():
                jobs.append(self.__jobs[i])
        return jobs
