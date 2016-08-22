# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-05-09
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
                         QCheckBox
                         # , QComboBox
                         )
from PyQt4.QtCore import QCoreApplication


class ProfileLayersDialog(QDialog):

    def __init__(self, pointLayers):
        """
        Constructor
        :param pointLayers: available points layers
        """
        QDialog.__init__(self)
        self.__pointLayers = pointLayers
        self.setWindowTitle(QCoreApplication.translate("VDLTools","Add Points Layers Profiles"))
        self.resize(300, 100)
        self.__layout = QGridLayout()
        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools","OK"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools","Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layersLabel = QLabel(QCoreApplication.translate("VDLTools","Also points layers profile ? :"))
        self.__layersLabel.setMinimumHeight(20)
        self.__layersLabel.setMinimumWidth(50)

        self.__layout.addWidget(self.__layersLabel, 0, 0, 1, 4)

        self.__layLabels = []
        self.__layChecks = []
        # self.__layCombos = []
        # self.__fieldsNames = []

        for i in xrange(len(self.__pointLayers)):
            label = QLabel(self.__pointLayers[i].name() + " :")
            label.setMinimumHeight(20)
            label.setMinimumWidth(50)
            self.__layLabels.append(label)
            self.__layout.addWidget(self.__layLabels[i], i+1, 1)
            check = QCheckBox()
            check.setChecked(True)
            self.__layChecks.append(check)
            self.__layout.addWidget(self.__layChecks[i], i+1, 2)
            # fields = self.__pointLayers[i].pendingFields()
            # if len(fields) > 0:
            #     combo = QComboBox()
            #     fieldsNames = []
            #     for f in fields:
            #         fieldsNames.append(f.name())
            #     self.__fieldsNames.append(fieldsNames)
            #     combo.addItems(fieldsNames)
            #     self.__layCombos.append(combo)
            #     self.__layout.addWidget(self.__layCombos[i], i+1, 3)
            #     self.__layChecks[i].stateChanged.connect(self.__attributesState)
            # else:
            #     self.__fieldsNames.append(None)
            #     self.__layCombos.append(None)
            #     self.__layChecks[i].setCheckState(False)
            #     self.__layChecks[i].setEnabled(False)

        self.__layout.addWidget(self.__okButton, 100, 1)
        self.__layout.addWidget(self.__cancelButton, 100, 2)

        self.setLayout(self.__layout)

    # def __attributesState(self):
    #     for i in xrange(len(self.__layChecks)):
    #         if self.__layCombos[i] is not None:
    #             self.__layCombos[i].setEnabled(self.__layChecks[i].isChecked())

    # def getLayersAndAttributes(self):
    #     layers = []
    #     attributes = []
    #     for i in xrange(len(self.__pointLayers)):
    #         if self.__layChecks[i].isChecked():
    #             layers.append(self.__pointLayers[i])
    #             attributes.append(self.__fieldsNames[i][self.__layCombos[i].currentIndex()])
    #     return layers, attributes

    def getLayers(self):
        """
        To get the selected points layers
        :return: selected points layers
        """
        layers = []
        for i in xrange(len(self.__pointLayers)):
            if self.__layChecks[i].isChecked():
                layers.append(self.__pointLayers[i])
        return layers

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

    # def close(self):
    #     for i in xrange(len(self.__layChecks)):
    #         if self.__layCombos[i] is not None:
    #             self.__layChecks[i].stateChanged.disconnect()
    #     QDialog.close(self)
