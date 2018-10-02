# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2018-09-04
        git sha              : $Format:%H$
        copyright            : (C) 2018 Ville de Lausanne
        author               : Ingénierie Informatique Gusthiot, Christophe Gusthiot
        email                : i2g@gusthiot.ch
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
from future.builtins import str
from future.builtins import range

from PyQt4.QtGui import (QDialog,
                         QWidget,
                         QScrollArea,
                         QGridLayout,
                         QPushButton,
                         QLabel,
                         QCheckBox)
from PyQt4.QtCore import QCoreApplication


class DrawdownMessageDialog(QDialog):
    """
    Dialog class to display the issues in the profile
    """

    def __init__(self, adjustments):
        """
        Constructor
        """
        QDialog.__init__(self)
        self.__adjustements = adjustments
        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Elevations adjustments"))
        self.__layout = QGridLayout()

        self.__msgLabels = []
        self.__msgChecks = []

        displayButton = False

        self.__scrollLayout = QGridLayout()

        for i in range(len(self.__adjustements)):
            adj = self.__adjustements[i]
            msg = "vertex " + str(adj['point']) + " : previous alt : " + str(adj['previous']) + ", max high : "
            msg += str(adj['diam']) + ", drawdown : " + str(adj['drawdown'])
            if adj['alt'] is not None:
                msg += ", new alt : " + str(adj['alt'])
            if adj['layer'] is not None:
                msg += " from " + adj['layer']
            msgLabel = QLabel(msg)
            self.__msgLabels.append(msgLabel)
            self.__scrollLayout.addWidget(self.__msgLabels[i], i+1, 0, 1, 2)
            msgCheck = QCheckBox()
            msgCheck.setChecked(True)
            self.__msgChecks.append(msgCheck)
            self.__scrollLayout.addWidget(self.__msgChecks[i], i+1, 2)
            displayButton = True

        widget = QWidget()
        widget.setLayout(self.__scrollLayout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)

        self.__layout.addWidget(scroll, 1, 0, 1, 3)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools", "Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        pos = len(self.__adjustements) + 1
        self.__layout.addWidget(self.__cancelButton, pos, 0)

        self.__applyButton = QPushButton(QCoreApplication.translate("VDLTools", "Apply drawdown"))
        self.__applyButton.setMinimumHeight(20)
        self.__applyButton.setMinimumWidth(100)
        if displayButton:
            self.__layout.addWidget(self.__applyButton, pos, 1)


        self.setLayout(self.__layout)


    def getAdjusts(self):
        """
        To get selected adjustments to apply
        :return: adjustments list
        """
        adjusts = []
        for i in range(len(self.__adjustements)):
            if self.__msgChecks[i] is not None and self.__msgChecks[i].isChecked():
                adjusts.append(self.__adjustements[i])
        return adjusts

    def cancelButton(self):
        """
        To get the cancel button instance
        :return: cancel button instance
        """
        return self.__cancelButton

    def applyButton(self):
        """
        To get the apply button instance
        :return: apply button instance
        """
        return self.__applyButton
