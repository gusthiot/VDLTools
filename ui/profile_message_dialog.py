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

from PyQt4.QtGui import (QDialog, QGridLayout, QPushButton, QLabel, QCheckBox)


class ProfileMessageDialog(QDialog):
    def __init__(self, situations, names, points):
        QDialog.__init__(self)
        self.__situations = situations
        self.__names = names
        self.__points = points
        self.resize(300, 100)
        self.__layout = QGridLayout()

        self.__msgLabels = []
        self.__msgChecks = []

        for i in xrange(len(self.__situations)):
            line = self.__situations[i]
            ptz = self.__points[line['point']]['z']
            msg = "- point {} in layer '{}' (point: {}m | line vertex: {}m) \n"\
                .format(line['point'], self.__names[line['layer']], ptz[line['layer']], ptz[0])
            msgLabel = QLabel(msg)
            self.__msgLabels.append(msgLabel)
            print(i+1)
            self.__layout.addWidget(self.__msgLabels[i], i+1, 0, 1, 2)
            msgCheck = QCheckBox()
            msgCheck.setChecked(True)
            self.__msgChecks.append(msgCheck)
            self.__layout.addWidget(self.__msgChecks[i], i+1, 2)

        self.__passButton = QPushButton("Pass")
        self.__passButton.setMinimumHeight(20)
        self.__passButton.setMinimumWidth(100)

        self.__onPointsButton = QPushButton("Apply line elevations to points")
        self.__onPointsButton.setMinimumHeight(20)
        self.__onPointsButton.setMinimumWidth(200)

        self.__onLineButton = QPushButton("Apply points elevations to line")
        self.__onLineButton.setMinimumHeight(20)
        self.__onLineButton.setMinimumWidth(200)

        pos = len(self.__situations) + 1
        self.__layout.addWidget(self.__passButton, pos, 0)
        self.__layout.addWidget(self.__onLineButton, pos, 1)
        self.__layout.addWidget(self.__onPointsButton, pos, 2)

        self.setLayout(self.__layout)

    def getSituations(self):
        situations = []
        for i in xrange(len(self.__situations)):
            if self.__msgChecks[i].isChecked():
                situations.append(self.__situations[i])
        return situations


    def passButton(self):
        return self.__passButton

    def onPointsButton(self):
        return self.__onPointsButton

    def onLineButton(self):
        return self.__onLineButton
