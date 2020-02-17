# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-06-13
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
from builtins import range
from qgis.PyQt.QtWidgets import (QDialog,
                                 QWidget,
                                 QScrollArea,
                                 QButtonGroup,
                                 QGridLayout,
                                 QRadioButton,
                                 QPushButton,
                                 QLabel)
from qgis.PyQt.QtCore import QCoreApplication


class InterpolateConfirmDialog(QDialog):
    """
    Dialog class to confirm the interpolation
    """

    def __init__(self):
        """
        Constructor
        """
        QDialog.__init__(self)
        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Edition Confirmation"))
        self.__layout = QGridLayout()

        self.__confirmLabel = QLabel(
            QCoreApplication.translate("VDLTools", "This LineString layer is not editable, what do you want to do ?"))

        self.__layout.addWidget(self.__confirmLabel, 0, 0, 1, 2)

        self.__radios = []

        self.__radios.append(QRadioButton(
            QCoreApplication.translate("VDLTools", "Create point, and edit line with new vertex")))
        self.__radios.append(QRadioButton(QCoreApplication.translate("VDLTools", "Create only the point")))
        self.__radios.append(QRadioButton(QCoreApplication.translate("VDLTools", "Just edit line with new vertex")))

        self.__scrollLayout = QGridLayout()

        self.__radios[0].setChecked(True)
        self.__radio_button_group = QButtonGroup()
        for i in range(len(self.__radios)):
            self.__scrollLayout.addWidget(self.__radios[i], i+1, 0, 1, 2)
            self.__radio_button_group.addButton(self.__radios[i], i)

        widget = QWidget()
        widget.setLayout(self.__scrollLayout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)

        self.__layout.addWidget(scroll, 1, 0, 1, 2)

        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools", "OK"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__layout.addWidget(self.__okButton, 4, 0)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools", "Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout.addWidget(self.__cancelButton, 4, 1)

        self.setLayout(self.__layout)

    def setMainLabel(self, label):
        """
        To set the title
        :param label: title
        """
        self.__confirmLabel.setText(label)

    def setAllLabel(self, label):
        """
        To set the all button title
        :param label: title
        """
        self.__radios[0].setText(label)

    def setVtLabel(self, label):
        """
        To set the vertex button title
        :param label: title
        """
        self.__radios[2].setText(label)

    def getCheckedId(self):
        """
        To get the radio button checked id
        0 : all
        1 : point
        2 : vertex
        :return: id of radion button
        """
        return self.__radio_button_group.checkedId()

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
