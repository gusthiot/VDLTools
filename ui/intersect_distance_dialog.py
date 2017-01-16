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
from builtins import str

from PyQt4.QtGui import (QDialog,
                         QGridLayout,
                         QPushButton,
                         QLabel,
                         QLineEdit,
                         QDoubleSpinBox)
from PyQt4.QtCore import QCoreApplication


class IntersectDistanceDialog(QDialog):
    """
    Dialog class to choose the circle radius
    """

    def __init__(self, mapPoint):
        """
        Constructor
        :param mapPoint: map point intersection
        """
        QDialog.__init__(self)
        self.__mapPoint = mapPoint
        self.setWindowTitle(QCoreApplication.translate("VDLTools","Choose radius"))
        self.resize(275, 177)
        self.__gridLayout = QGridLayout()

        self.__label = QLabel(QCoreApplication.translate("VDLTools","Radius"))
        self.__gridLayout.addWidget(self.__label, 2, 1, 1, 1)

        self.__observation = QDoubleSpinBox()
        self.__observation.setDecimals(4)
        self.__observation.setMaximum(999999.99)
        self.__observation.setSingleStep(1.0)
        self.__gridLayout.addWidget(self.__observation, 2, 2, 1, 1)

        self.__label_3 = QLabel("m")
        self.__gridLayout.addWidget(self.__label_3, 2, 3, 1, 1)

        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools","OK"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools","Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__gridLayout.addWidget(self.__okButton, 5, 1)
        self.__gridLayout.addWidget(self.__cancelButton, 5, 2)

        self.__label_5 = QLabel("y")
        self.__gridLayout.addWidget(self.__label_5, 1, 1, 1, 1)

        self.__label_6 = QLabel("x")
        self.__gridLayout.addWidget(self.__label_6, 0, 1, 1, 1)

        self.__x = QLineEdit("x")
        self.__x.setText(str(self.__mapPoint.x()))
        self.__x.setEnabled(False)
        self.__gridLayout.addWidget(self.__x, 0, 2, 1, 2)

        self.__y = QLineEdit("y")
        self.__y.setText(str(self.__mapPoint.y()))
        self.__y.setEnabled(False)
        self.__gridLayout.addWidget(self.__y, 1, 2, 1, 2)

        self.setLayout(self.__gridLayout)

    def observation(self):
        """
        To get the circle radius edit widget
        :return: circle radius edit widget
        """
        return self.__observation

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

    def mapPoint(self):
        """
        To get the map point intersection
        :return: map point intersection
        """
        return self.__mapPoint

