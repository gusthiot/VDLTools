# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-05-30
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
from builtins import range

from qgis.PyQt.QtWidgets import QDialog, QWidget, QScrollArea, QGridLayout, QPushButton, QLabel, QCheckBox
from qgis.PyQt.QtCore import QCoreApplication


class ProfileMessageDialog(QDialog):
    """
    Dialog class to display the issues in the profile
    """

    def __init__(self, situations, differences, names, points):
        """
        Constructor
        :param situations: situations, when point and vertex elevations are different
        :param differences: when lines vertex elevations are different on position connection
        :param names: layers names
        :param points: vertices positions
        """
        QDialog.__init__(self)
        self.__situations = situations
        self.__differences = differences
        self.__names = names
        num_lines = len(points[0]['z']) - len(names) + 1
        self.__points = points
        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Elevations situations"))
        self.__layout = QGridLayout()

        self.__msgLabels = []
        self.__msgChecks = []
        self.__difLabels = []

        self.__scrollLayout = QGridLayout()

        for i in range(len(self.__situations)):
            line = self.__situations[i]
            ptz = self.__points[line['point']]['z'][line['layer']+num_lines-1]
            if 'poz' in line:
                ptz = ptz[line['poz']]
            msg = "- point " + str(line['point']) + QCoreApplication.translate("VDLTools", " in layer '") + \
                  self.__names[line['layer']] + "' (point: " + str(ptz) + "m |" + \
                  QCoreApplication.translate("VDLTools", "line vertex: ") + str(line['vertex']) + "m) \n"

            msgLabel = QLabel(msg)
            self.__msgLabels.append(msgLabel)
            self.__scrollLayout.addWidget(self.__msgLabels[i], i+1, 0, 1, 2)
            msgCheck = QCheckBox()
            msgCheck.setChecked(True)
            self.__msgChecks.append(msgCheck)
            self.__scrollLayout.addWidget(self.__msgChecks[i], i+1, 2)

        for i in range(len(self.__differences)):
            line = self.__differences[i]
            msg = "- point " + str(line['point']) + \
                  QCoreApplication.translate("VDLTools", " in layer : different elevations on same position ") + "(" +\
                  str(line['v1']) + "m and" + str(line['v2']) + "m) \n"
            difLabel = QLabel(msg)
            self.__difLabels.append(difLabel)
            self.__scrollLayout.addWidget(self.__difLabels[i], len(self.__situations) + (i+1), 0, 1, 2)


        widget = QWidget()
        widget.setLayout(self.__scrollLayout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)

        self.__layout.addWidget(scroll, 1, 0, 1, 3)

        self.__passButton = QPushButton(QCoreApplication.translate("VDLTools", "Pass"))
        self.__passButton.setMinimumHeight(20)
        self.__passButton.setMinimumWidth(100)

        pos = len(self.__situations) + len(self.__differences) + 1
        self.__layout.addWidget(self.__passButton, pos, 0)

        self.__onPointsButton = QPushButton(QCoreApplication.translate("VDLTools", "Apply line elevations to points"))
        self.__onPointsButton.setMinimumHeight(20)
        self.__onPointsButton.setMinimumWidth(200)

        self.__onLineButton = QPushButton(QCoreApplication.translate("VDLTools", "Apply points elevations to line"))
        self.__onLineButton.setMinimumHeight(20)
        self.__onLineButton.setMinimumWidth(200)

        if len(self.__situations) > 0:
            self.__layout.addWidget(self.__onLineButton, pos, 1)
            self.__layout.addWidget(self.__onPointsButton, pos, 2)

        self.setLayout(self.__layout)

    def getSituations(self):
        """
        To get the checked situations
        :return: checked situations
        """
        situations = []
        for i in range(len(self.__situations)):
            if self.__msgChecks[i].isChecked():
                situations.append(self.__situations[i])
        return situations

    def passButton(self):
        """
        To get the pass button instance
        :return: pass button instance
        """
        return self.__passButton

    def onPointsButton(self):
        """
        To get the on points button instance
        :return: on points button instance
        """
        return self.__onPointsButton

    def onLineButton(self):
        """
        To get the on line button instance
        :return: on line button instance
        """
        return self.__onLineButton
