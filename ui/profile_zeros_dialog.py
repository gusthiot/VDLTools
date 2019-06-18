# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-11-01
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


class ProfileZerosDialog(QDialog):
    """
    """

    def __init__(self, zeros):
        """
        Constructor
        """
        QDialog.__init__(self)
        self.__zeros = zeros
        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Zeros"))
        self.__layout = QGridLayout()

        self.__zeroLabels = []
        self.__zeroChecks = []

        displayButton = False

        self.__scrollLayout = QGridLayout()

        for i in range(len(self.__zeros)):
            msg = "- vertex " + str(self.__zeros[i][0])
            msg += QCoreApplication.translate("VDLTools", ", elevation : '0', ")
            if self.__zeros[i][1] is not None:
                print(self.__zeros[i])
                if self.__zeros[i][3] == 'E':
                    msg += QCoreApplication.translate("VDLTools", "extrapolated elevation : ")
                else:
                    msg += QCoreApplication.translate("VDLTools", "interpolated elevation : ")
                msg += str(self.__zeros[i][1]) + "m"
                if self.__zeros[i][2] > 1:
                    msg += QCoreApplication.translate("VDLTools", " (and apply to point)")
                msgCheck = QCheckBox()
                msgCheck.setChecked(True)
                self.__zeroChecks.append(msgCheck)
                self.__scrollLayout.addWidget(self.__zeroChecks[i], i+1, 2)
                displayButton = True
            else:
                print(self.__zeros[i])
                if self.__zeros[i][3] == 'E':
                    msg += QCoreApplication.translate("VDLTools", "no extrapolated elevation")
                else:
                    msg += QCoreApplication.translate("VDLTools", "no interpolated elevation")
                self.__zeroChecks.append(None)

            zeroLabel = QLabel(msg)
            self.__zeroLabels.append(zeroLabel)
            self.__scrollLayout.addWidget(self.__zeroLabels[i], i+1, 0, 1, 2)

        widget = QWidget()
        widget.setLayout(self.__scrollLayout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)

        self.__layout.addWidget(scroll, 1, 0, 1, 2)

        self.__passButton = QPushButton(QCoreApplication.translate("VDLTools", "Pass"))
        self.__passButton.setMinimumHeight(20)
        self.__passButton.setMinimumWidth(100)

        pos = len(self.__zeros) + 1
        self.__layout.addWidget(self.__passButton, pos, 0)

        self.__applyButton = QPushButton(QCoreApplication.translate("VDLTools", "Apply adjustments"))
        self.__applyButton.setMinimumHeight(20)
        self.__applyButton.setMinimumWidth(100)
        if displayButton:
            self.__layout.addWidget(self.__applyButton, pos, 1)

        self.setLayout(self.__layout)

    def getZeros(self):
        """
        To get selected zeros to interpolate
        :return: zeros list
        """
        zeros = []
        for i in range(len(self.__zeros)):
            if self.__zeroChecks[i] is not None and self.__zeroChecks[i].isChecked():
                zeros.append(self.__zeros[i])
        return zeros

    def passButton(self):
        """
        To get the pass button instance
        :return: pass button instance
        """
        return self.__passButton

    def applyButton(self):
        """
        To get the apply button instance
        :return: apply button instance
        """
        return self.__applyButton
