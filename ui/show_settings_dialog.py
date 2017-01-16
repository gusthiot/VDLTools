# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-06-20
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
from __future__ import print_function
from builtins import next


from PyQt4.QtGui import (QDialog,
                         QLineEdit,
                         QGridLayout,
                         QPushButton,
                         QLabel,
                         QComboBox)
from qgis.core import (QgsMapLayer,
                       QgsMapLayerRegistry,
                       QGis)
from PyQt4.QtCore import QCoreApplication
from ..core.db_connector import DBConnector


class ShowSettingsDialog(QDialog):
    """
    Dialog class for plugin settings
    """

    def __init__(self, iface, memoryPointsLayer, memoryLinesLayer, configTable, uriDb, schemaDb, mntUrl):
        """
        Constructor
        :param iface: interface
        :param memoryPointsLayer: working memory points layer
        :param memoryLinesLayer: working memory lines layer
        :param configTable: config table selected for import
        """
        QDialog.__init__(self)
        self.__iface = iface
        self.__memoryPointsLayer = memoryPointsLayer
        self.__memoryLinesLayer = memoryLinesLayer
        self.__configTable = configTable
        self.__uriDb = uriDb
        self.__schemaDb = schemaDb
        self.__mntUrl = mntUrl
        self.setWindowTitle(QCoreApplication.translate("VDLTools","Settings"))
        self.__pointsLayers = []
        self.__linesLayers = []
        self.__tables = []
        self.__schemas = []
        self.__dbs = DBConnector.getUsedDatabases()

        for layer in list(QgsMapLayerRegistry.instance().mapLayers().values()):
            if layer is not None and layer.type() == QgsMapLayer.VectorLayer and layer.providerType() == "memory":
                if layer.geometryType() == QGis.Point:
                    self.__pointsLayers.append(layer)
                if layer.geometryType() == QGis.Line:
                    self.__linesLayers.append(layer)
        self.resize(450, 200)
        self.__layout = QGridLayout()

        pointLabel = QLabel(QCoreApplication.translate("VDLTools","Working points layer : "))
        pointLabel.setMinimumHeight(20)
        pointLabel.setMinimumWidth(50)
        self.__layout.addWidget(pointLabel, 0, 1)

        self.__pointCombo = QComboBox()
        self.__pointCombo.setMinimumHeight(20)
        self.__pointCombo.setMinimumWidth(50)
        self.__pointCombo.addItem("")
        for layer in self.__pointsLayers:
            self.__pointCombo.addItem(layer.name())
        self.__layout.addWidget(self.__pointCombo, 0, 2)
        self.__pointCombo.currentIndexChanged.connect(self.__pointComboChanged)
        if self.__memoryPointsLayer is not None:
            if self.__memoryPointsLayer in self.__pointsLayers:
                self.__pointCombo.setCurrentIndex(self.__pointsLayers.index(self.__memoryPointsLayer)+1)

        lineLabel = QLabel(QCoreApplication.translate("VDLTools","Working lines layer : "))
        lineLabel.setMinimumHeight(20)
        lineLabel.setMinimumWidth(50)
        self.__layout.addWidget(lineLabel, 1, 1)

        self.__lineCombo = QComboBox()
        self.__lineCombo.setMinimumHeight(20)
        self.__lineCombo.setMinimumWidth(50)
        self.__lineCombo.addItem("")
        for layer in self.__linesLayers:
            self.__lineCombo.addItem(layer.name())
        self.__layout.addWidget(self.__lineCombo, 1, 2)
        self.__lineCombo.currentIndexChanged.connect(self.__lineComboChanged)
        if self.__memoryLinesLayer is not None:
            if self.__memoryLinesLayer in self.__linesLayers:
                self.__lineCombo.setCurrentIndex(self.__linesLayers.index(self.__memoryLinesLayer)+1)

        dbLabel = QLabel(QCoreApplication.translate("VDLTools","Import database : "))
        dbLabel.setMinimumHeight(20)
        dbLabel.setMinimumWidth(50)
        self.__layout.addWidget(dbLabel, 2, 1)

        self.__dbCombo = QComboBox()
        self.__dbCombo.setMinimumHeight(20)
        self.__dbCombo.setMinimumWidth(50)
        self.__dbCombo.addItem("")
        for db in list(self.__dbs.keys()):
            self.__dbCombo.addItem(db)
        self.__layout.addWidget(self.__dbCombo, 2, 2)

        schemaLabel = QLabel(QCoreApplication.translate("VDLTools","Database schema : "))
        schemaLabel.setMinimumHeight(20)
        schemaLabel.setMinimumWidth(50)
        self.__layout.addWidget(schemaLabel, 3, 1)

        self.__schemaCombo = QComboBox()
        self.__schemaCombo.setMinimumHeight(20)
        self.__schemaCombo.setMinimumWidth(50)
        self.__schemaCombo.addItem("")
        self.__layout.addWidget(self.__schemaCombo, 3, 2)

        tableLabel = QLabel(QCoreApplication.translate("VDLTools","Config table : "))
        tableLabel.setMinimumHeight(20)
        tableLabel.setMinimumWidth(50)
        self.__layout.addWidget(tableLabel, 4, 1)

        self.__tableCombo = QComboBox()
        self.__tableCombo.setMinimumHeight(20)
        self.__tableCombo.setMinimumWidth(50)
        self.__tableCombo.addItem("")
        self.__layout.addWidget(self.__tableCombo, 4, 2)

        mntLabel = QLabel(QCoreApplication.translate("VDLTools","Url for MNT : "))
        schemaLabel.setMinimumHeight(20)
        schemaLabel.setMinimumWidth(50)
        self.__layout.addWidget(mntLabel, 5, 1)

        self.__mntText = QLineEdit()
        if self.__mntUrl is None or self.__mntUrl == "None":
            self.__mntText.insert('http://map.lausanne.ch/main/wsgi/profile.json')
        else:
            self.__mntText.insert(self.__mntUrl)
        self.__mntText.setMinimumHeight(20)
        self.__mntText.setMinimumWidth(100)
        self.__layout.addWidget(self.__mntText, 5, 2)


        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools","OK"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools","Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout.addWidget(self.__okButton, 100, 1)
        self.__layout.addWidget(self.__cancelButton, 100, 2)
        self.setLayout(self.__layout)

        self.__dbCombo.currentIndexChanged.connect(self.__dbComboChanged)
        self.__schemaCombo.currentIndexChanged.connect(self.__schemaComboChanged)
        self.__tableCombo.currentIndexChanged.connect(self.__tableComboChanged)
        if self.__uriDb is not None:
            if self.__uriDb.database() in list(self.__dbs.keys()):
                self.__dbCombo.setCurrentIndex(list(self.__dbs.keys()).index(self.__uriDb.database()) + 1)

    @staticmethod
    def __resetCombo(combo):
        while combo.count() > 0:
            combo.removeItem(combo.count()-1)

    def __setSchemaCombo(self, uriDb):
        connector = DBConnector(uriDb, self.__iface)
        db = connector.setConnection()
        if db:
            self.__schemaCombo.currentIndexChanged.disconnect(self.__schemaComboChanged)
            self.__resetCombo(self.__schemaCombo)
            self.__schemaCombo.addItem("")
            self.__schemas = []
            query = db.exec_("""SELECT DISTINCT table_schema FROM information_schema.tables WHERE table_schema NOT IN
                ('pg_catalog', 'information_schema', 'topology') AND table_type = 'BASE TABLE' AND table_name NOT IN
                (SELECT f_table_name FROM geometry_columns)""")
            if query.lastError().isValid():
                print(query.lastError().text())
            else:
                while next(query):
                    self.__schemas.append(query.value(0))
                db.close()
                for schema in self.__schemas:
                    self.__schemaCombo.addItem(schema)
                self.__schemaCombo.currentIndexChanged.connect(self.__schemaComboChanged)
                if self.__schemaDb is not None:
                    if self.__schemaDb in self.__schemas:
                        self.__schemaCombo.setCurrentIndex(self.__schemas.index(self.__schemaDb) + 1)

    def __setTableCombo(self, uriDb, schema):
        connector = DBConnector(uriDb, self.__iface)
        db = connector.setConnection()
        if db:
            self.__tableCombo.currentIndexChanged.disconnect(self.__tableComboChanged)
            self.__resetCombo(self.__tableCombo)
            self.__tableCombo.addItem("")
            self.__tables = []
            query = db.exec_("""SELECT table_name FROM information_schema.tables WHERE table_schema = '""" + schema +
                             """' ORDER BY table_name""")
            if query.lastError().isValid():
                print(query.lastError().text())
            else:
                while next(query):
                    self.__tables.append(query.value(0))
                db.close()
                for table in self.__tables:
                    if self.__tableCombo.findText(table) == -1:
                        self.__tableCombo.addItem(table)
                self.__tableCombo.currentIndexChanged.connect(self.__tableComboChanged)
                if self.__configTable is not None:
                    if self.__configTable in self.__tables:
                        self.__tableCombo.setCurrentIndex(self.__tables.index(self.__configTable) + 1)

    def __lineComboChanged(self):
        """
        To remove blank item when another one is selected
        """
        if self.__lineCombo.itemText(0) == "":
            self.__lineCombo.removeItem(0)

    def __pointComboChanged(self):
        """
        To remove blank item when another one is selected
        """
        if self.__pointCombo.itemText(0) == "":
            self.__pointCombo.removeItem(0)

    def __tableComboChanged(self):
        """
        To remove blank item when another one is selected
        """
        if self.__tableCombo.itemText(0) == "":
            self.__tableCombo.removeItem(0)

    def __dbComboChanged(self):
        if self.__dbCombo.itemText(0) == "":
            self.__dbCombo.removeItem(0)
        if self.uriDb() is not None:
            self.__setSchemaCombo(self.uriDb())

    def __schemaComboChanged(self):
        if self.__schemaCombo.itemText(0) == "":
            self.__schemaCombo.removeItem(0)
        if self.schemaDb() is not None:
            self.__setTableCombo(self.uriDb(), self.schemaDb())


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

    def pointsLayer(self):
        """
        To get the selected memory points layer
        :return: selected memeory points layer, or none
        """
        index = self.__pointCombo.currentIndex()
        if self.__pointCombo.itemText(index) == "":
            return None
        else:
            return self.__pointsLayers[index]

    def linesLayer(self):
        """
        To get the selected memory lines layer
        :return: selected memory lines layer, or none
        """
        index = self.__lineCombo.currentIndex()
        if self.__lineCombo.itemText(index) == "":
            return None
        else:
            return self.__linesLayers[index]

    def configTable(self):
        """
        To get the selected config table
        :return: selected config table, or none
        """
        index = self.__tableCombo.currentIndex()
        if self.__tableCombo.itemText(index) == "":
            return None
        else:
            return self.__tables[index]

    def uriDb(self):
        index = self.__dbCombo.currentIndex()
        if self.__dbCombo.itemText(index) == "":
            return None
        else:
            return self.__dbs[list(self.__dbs.keys())[index]]

    def schemaDb(self):
        index = self.__schemaCombo.currentIndex()
        if self.__schemaCombo.itemText(index) == "":
            return None
        else:
            return self.__schemas[index]

    def mntUrl(self):
        return self.__mntText.text()
