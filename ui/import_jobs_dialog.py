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
        self.setWindowTitle(QCoreApplication.translate("VDLTools","What to process (radio button does nothing for now)"))
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

        jobButton = QRadioButton(QCoreApplication.translate("VDLTools","Job(s)"))
        self.__layout.addWidget(jobButton, 0, 1)
        self.__group.addButton(jobButton)

        self.__jobsLabels = []
        self.__jobsChecks = []

        for i in range(len(self.__jobs)):
            label = QLabel(jobs[i])
            label.setMinimumHeight(20)
            label.setMinimumWidth(50)
            self.__jobsLabels.append(label)
            self.__layout.addWidget(self.__jobsLabels[i], i+1, 1)
            check = QCheckBox()
            check.setChecked(False)
            self.__jobsChecks.append(check)
            self.__layout.addWidget(self.__jobsChecks[i], i+1, 2)

        pointsButton = QRadioButton(QCoreApplication.translate("VDLTools","Selected Point(s)"))
        self.__layout.addWidget(pointsButton, len(self.__jobs)+2, 1)
        self.__group.addButton(pointsButton)

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
