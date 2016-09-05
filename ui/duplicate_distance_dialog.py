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
                         QCheckBox,
                         QLabel,
                         QLineEdit,
                         QDoubleValidator,
                         QRadioButton,
                         QButtonGroup)
from PyQt4.QtCore import QCoreApplication


class DuplicateDistanceDialog(QDialog):

    def __init__(self, isComplexPolygon):
        """
        Constructor
        :param isComplexPolygon: for a polygon, if it has interior ring(s)
        """
        QDialog.__init__(self)
        self.setWindowTitle(QCoreApplication.translate("VDLTools","Duplicate"))
        self.resize(300, 100)
        self.__distanceLabel = QLabel(QCoreApplication.translate("VDLTools","distance :"))
        self.__distanceLabel.setMinimumHeight(20)
        self.__distanceLabel.setMinimumWidth(50)

        self.__distanceEdit = QLineEdit("inputMask")
        self.__distanceEdit.setMinimumHeight(20)
        self.__distanceEdit.setMinimumWidth(120)
        self.__distanceEdit.setValidator(QDoubleValidator(-1000, 1000, 4, self))

        self.__distanceDirection = QCheckBox(QCoreApplication.translate("VDLTools","invert direction"))

        self.__previewButton = QPushButton(QCoreApplication.translate("VDLTools","Preview"))
        self.__previewButton.setMinimumHeight(20)
        self.__previewButton.setMinimumWidth(100)

        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools","OK"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools","Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout = QGridLayout()
        self.__layout.addWidget(self.__distanceLabel, 0, 0)
        self.__layout.addWidget(self.__distanceEdit, 0, 1)
        self.__layout.addWidget(self.__distanceDirection, 0, 2)

        if isComplexPolygon:
            self.__polygonLabel = QLabel(
                QCoreApplication.translate("VDLTools","In which direction the internal part has to be duplicated ?"))
            self.__polygonLabel.setMinimumHeight(20)
            self.__polygonLabel.setMinimumWidth(50)
            self.__layout.addWidget(self.__polygonLabel, 1, 0, 1, 3)

            self.__directions = [QRadioButton(QCoreApplication.translate("VDLTools","same")),
                                 QRadioButton(QCoreApplication.translate("VDLTools","opposite"))]
            self.__directions[0].setChecked(True)
            self.__direction_button_group = QButtonGroup()
            for i in xrange(len(self.__directions)):
                self.__layout.addWidget(self.__directions[i], 2, i+1)
                self.__direction_button_group.addButton(self.__directions[i], i)

        self.__layout.addWidget(self.__previewButton, 3, 0)
        self.__layout.addWidget(self.__okButton, 3, 1)
        self.__layout.addWidget(self.__cancelButton, 3, 2)
        self.setLayout(self.__layout)

    def previewButton(self):
        """
        To get the preview button instance
        :return: preview button instance
        """
        return self.__previewButton

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

    def distanceEdit(self):
        """
        To get the distance edit widget
        :return: distance edit widget
        """
        return self.__distanceEdit

    def isDirectionInverted(self):
        return self.__distanceDirection.checkState()

    def distanceEditText(self):
        """
        To get the text putted into the distance edit field
        :return: text from ditance edit field
        """
        return self.__distanceEdit.text()

    def setDistanceEditText(self, text):
        """
        To set the distance displayed in the distance edit field
        """
        self.__distanceEdit.setText(text)

    def isInverted(self):
        """
        To get if the user want a complex polygon duplication inverted or not
        :return: true if inverted, false otherwise
        """
        return self.__direction_button_group.checkedId() == 1
