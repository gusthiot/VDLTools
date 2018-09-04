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

        self.__scrollLayout = QGridLayout()

        for i in range(len(self.__adjustements)):
            msgLabel = QLabel(self.__adjustements[i])
            self.__msgLabels.append(msgLabel)
            self.__scrollLayout.addWidget(self.__msgLabels[i], i+1, 0, 1, 2)

        widget = QWidget()
        widget.setLayout(self.__scrollLayout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)

        self.__layout.addWidget(scroll, 1, 0, 1, 3)

        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools", "OK"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        pos = len(self.__adjustements) + 1
        self.__layout.addWidget(self.__okButton, pos, 0)

        self.setLayout(self.__layout)

    def okButton(self):
        """
        To get the pass button instance
        :return: pass button instance
        """
        return self.__okButton
