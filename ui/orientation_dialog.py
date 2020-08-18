# -*- coding: utf-8 -*-

#-----------------------------------------------------------
#
# Intersect It is a QGIS plugin to place observations (distance or orientation)
# with their corresponding precision, intersect them using a least-squares solution
# and save dimensions in a dedicated layer to produce maps.
#
# Copyright    : (C) 2013 Denis Rouzaud
# Email        : denis.rouzaud@gmail.com
#
#-----------------------------------------------------------
#
# licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this progsram; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#---------------------------------------------------------------------
"""
Reimplemented for QGIS3 by :

/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2020-08-07
        git sha              : $Format:%H$
        copyright            : (C) 2020 Ville de Lausanne
        author               : Christophe Gusthiot
        email                : i2g@gusthiot.ch
 ***************************************************************************/
"""

from qgis.PyQt.QtWidgets import (QDialog,
                                 QPushButton,
                                 QDoubleSpinBox,
                                 QGridLayout,
                                 QLabel)
from qgis.PyQt.QtCore import QCoreApplication


class OrientationDialog(QDialog):
    """
    Dialog class to choose the settings for placing orientation
    """

    def __init__(self, orientation, rubber
                 #, settings
                ):
        """
        Constructor
        """
        QDialog.__init__(self)
        self.__orientation = orientation
        self.__rubber = rubber
        # self.__settings = settings

        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Place Orientation"))
        self.__layout = QGridLayout()

        # self.__precisionLabel = QLabel(QCoreApplication.translate("VDLTools", "Precision of prolongation [°]"))
        # self.__layout.addWidget(self.__precisionLabel, 0, 0)
        #
        # self.__precisionSpinBox = QDoubleSpinBox()
        # self.__precisionSpinBox.setDecimals(4)
        # self.__precisionSpinBox.setMaximum(10.0)
        # self.__precisionSpinBox.setSingleStep(0.05)
        # if self.__settings.orientPrecision is not None:
        #     self.__precisionSpinBox.setValue(self.__settings.orientPrecision)
        # else:
        # self.__precisionSpinBox.setValue(0.5)
        # self.__layout.addWidget(self.__precisionSpinBox, 0, 1)

        self.__lengthLabel = QLabel(QCoreApplication.translate("VDLTools", "Length of drawn line"))
        self.__layout.addWidget(self.__lengthLabel, 1, 0)

        self.__lengthSpinBox = QDoubleSpinBox()
        self.__lengthSpinBox.setDecimals(2)
        # if self.__settings.orientLength is not None:
        #     self.__lengthSpinBox.setValue(self.__settings.orientLength)
        # else:
        self.__lengthSpinBox.setValue(8.0)
        self.__layout.addWidget(self.__lengthSpinBox, 1, 1)

        self.__angleLabel = QLabel(QCoreApplication.translate("VDLTools", "Angle [°]"))
        self.__layout.addWidget(self.__angleLabel, 2, 0)

        self.__angleSpinBox = QDoubleSpinBox()
        self.__angleSpinBox.setDecimals(3)
        self.__angleSpinBox.setMinimum(-180.0)
        self.__angleSpinBox.setMaximum(180.0)
        self.__angleSpinBox.setValue(orientation.azimut)
        self.__layout.addWidget(self.__angleSpinBox, 2, 1)

        # self.__precisionSpinBox.valueChanged.connect(self.changePrecision)
        self.__angleSpinBox.valueChanged.connect(self.changeAzimut)
        self.__lengthSpinBox.valueChanged.connect(self.changeLength)

        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools",  "OK"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools", "Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout.addWidget(self.__okButton, 3, 0)
        self.__layout.addWidget(self.__cancelButton, 3, 1)

        self.setLayout(self.__layout)

    def changeLength(self, length):
        """
        When te length is changed
        :param length: new length
        """
        self.__orientation.length = length
        self.__rubber.setToGeometry(self.__orientation.geometry(), None)

    def changeAzimut(self, angle):
        """
        When the angle is changed
        :param angle: new angle
        """
        self.__orientation.azimut = angle
        self.__rubber.setToGeometry(self.__orientation.geometry(), None)

    # def changePrecision(self, v):
    #     self.__orientation.precision = v

    def getOrientation(self):
        """
        To return the updated orientation object
        :return: orientation object
        """
        return self.__orientation

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
