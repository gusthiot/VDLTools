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
from future.builtins import next


from qgis.gui import QgsMessageBar
from PyQt4.QtGui import (QDialog,
                         QLineEdit,
                         QGridLayout,
                         QHBoxLayout,
                         QPushButton,
                         QLabel,
                         QCheckBox,
                         QWidget,
                         QComboBox)
from qgis.core import (QgsMapLayer,
                       QgsWKBTypes,
                       QgsMapLayerRegistry,
                       QGis)
from PyQt4.QtCore import QCoreApplication
from ..core.db_connector import DBConnector
from ..core.signal import Signal


class ShowSettingsDialog(QDialog):
    """
    Dialog class for plugin settings
    """

    def __init__(self, iface, memoryPointsLayer, memoryLinesLayer, importConfigTable, importUriDb, importSchemaDb,
                 controlConfigTable, controlUriDb, controlSchemaDb, mntUrl, refLayers, adjLayers, levelAtt, levelVal,
                 drawdowmLayer, pipeDiam, moreTools):
        """
        Constructor
        :param iface: interface
        :param memoryPointsLayer: working memory points layer
        :param memoryLinesLayer: working memory lines layer
        :param importConfigTable: config table selected for import
        :param importUriDb: database for import
        :param importSchemaDb: db schema for import
        :param controlConfigTable: config table selected for control
        :param controlUriDb: database for control
        :param controlSchemaDb: db schema for control
        :param mntUrl: url to get mnt
        :param refLayers: reference layers for drawdown
        :param adjLayers: adjustement layers for drawdown
        :param levelAtt: level attribute for drawdown
        :param levelVal: level value for drawdown
        :param drawdowmLayer: line layer for drawdown
        :param pipeDiam: pipe diameter for drawdown
        :param moreTools: if more tools or not
        """
        QDialog.__init__(self)
        self.__iface = iface
        self.__memoryPointsLayer = memoryPointsLayer
        self.__memoryLinesLayer = memoryLinesLayer
        self.__importConfigTable = importConfigTable
        self.__importUriDb = importUriDb
        self.__importSchemaDb = importSchemaDb
        self.__controlConfigTable = controlConfigTable
        self.__controlUriDb = controlUriDb
        self.__controlSchemaDb = controlSchemaDb
        self.__mntUrl = mntUrl
        self.__refLayers = refLayers
        self.__adjLayers = adjLayers
        self.__levelAtt = levelAtt
        self.__levelVal = levelVal
        self.__drawdowmLayer = drawdowmLayer
        self.__pipeDiam = pipeDiam
        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Settings"))
        self.__pointsLayers = []
        self.__linesLayers = []
        self.__refAvailableLayers = []
        self.__drawdownLayers = []
        self.__tables = []
        self.__schemas = []
        self.__pipeDiamFields = []
        self.__levelAttFields = []
        self.__dbs = DBConnector.getUsedDatabases()

        self.__refLabels = []
        self.__refChecks = []
        self.__adjChecks = []

        for layer in list(QgsMapLayerRegistry.instance().mapLayers().values()):
            if layer is not None and layer.type() == QgsMapLayer.VectorLayer:
                if layer.providerType() == "memory":
                    if layer.geometryType() == QGis.Point:
                        self.__pointsLayers.append(layer)
                    if layer.geometryType() == QGis.Line:
                        self.__linesLayers.append(layer)
                if QGis.fromOldWkbType(layer.wkbType()) == QgsWKBTypes.LineStringZ:
                    self.__drawdownLayers.append(layer)
                if QGis.fromOldWkbType(layer.wkbType()) == QgsWKBTypes.PointZ:
                    self.__refAvailableLayers.append(layer)

        self.resize(600, 500)
        self.__layout = QGridLayout()
        self.__scrollLayout = QGridLayout()
        line = 0

        intersectLabel = QLabel(QCoreApplication.translate("VDLTools", "Intersect "))
        self.__scrollLayout.addWidget(intersectLabel, line, 0)

        line += 1

        pointLabel = QLabel(QCoreApplication.translate("VDLTools", "Working points layer : "))
        self.__scrollLayout.addWidget(pointLabel, line, 1)

        self.__pointCombo = QComboBox()
        self.__pointCombo.setMinimumHeight(20)
        self.__pointCombo.setMinimumWidth(50)
        self.__pointCombo.addItem("")
        for layer in self.__pointsLayers:
            self.__pointCombo.addItem(layer.name())
        self.__scrollLayout.addWidget(self.__pointCombo, line, 2)
        self.__pointCombo.currentIndexChanged.connect(self.__pointComboChanged)
        if self.__memoryPointsLayer is not None:
            if self.__memoryPointsLayer in self.__pointsLayers:
                self.__pointCombo.setCurrentIndex(self.__pointsLayers.index(self.__memoryPointsLayer)+1)

        line += 1

        lineLabel = QLabel(QCoreApplication.translate("VDLTools", "Working lines layer : "))
        self.__scrollLayout.addWidget(lineLabel, line, 1)

        self.__lineCombo = QComboBox()
        self.__lineCombo.setMinimumHeight(20)
        self.__lineCombo.setMinimumWidth(50)
        self.__lineCombo.addItem("")
        for layer in self.__linesLayers:
            self.__lineCombo.addItem(layer.name())
        self.__scrollLayout.addWidget(self.__lineCombo, line, 2)
        self.__lineCombo.currentIndexChanged.connect(self.__lineComboChanged)
        if self.__memoryLinesLayer is not None:
            if self.__memoryLinesLayer in self.__linesLayers:
                self.__lineCombo.setCurrentIndex(self.__linesLayers.index(self.__memoryLinesLayer)+1)

        line += 1

        profilesLabel = QLabel(QCoreApplication.translate("VDLTools", "Profiles "))
        self.__scrollLayout.addWidget(profilesLabel, line, 0)

        line += 1

        mntLabel = QLabel(QCoreApplication.translate("VDLTools", "Url for MNT : "))
        self.__scrollLayout.addWidget(mntLabel, line, 1)

        self.__mntText = QLineEdit()
        if self.__mntUrl is None or self.__mntUrl == "None":
            self.__mntText.insert('https://map.lausanne.ch/prod/wsgi/profile.json')
        else:
            self.__mntText.insert(self.__mntUrl)
        self.__mntText.setMinimumHeight(20)
        self.__mntText.setMinimumWidth(100)
        self.__scrollLayout.addWidget(self.__mntText, line, 2)

        line += 1

        ddLabel = QLabel(QCoreApplication.translate("VDLTools", "Drawdown "))
        self.__scrollLayout.addWidget(ddLabel, line, 0)

        line += 1

        self.__scrollLayout.addWidget(QLabel(QCoreApplication.translate("VDLTools", "Layer")), line, 1)

        namesLayout = QHBoxLayout()
        namesWidget = QWidget()
        namesLayout.addWidget(QLabel(QCoreApplication.translate("VDLTools", "Reference")))
        namesLayout.addWidget(QLabel(QCoreApplication.translate("VDLTools", "Adjustable")))
        namesLayout.setContentsMargins(0,0,0,0)
        namesWidget.setLayout(namesLayout)
        self.__scrollLayout.addWidget(namesWidget, line, 2)

        line += 1

        for layer in self.__refAvailableLayers:
            refLabel = QLabel("  - " + layer.name())
            self.__refLabels.append(refLabel)
            self.__scrollLayout.addWidget(refLabel, line, 1)

            checksLayout = QHBoxLayout()
            checksLayout.setContentsMargins(0,0,0,0)
            checksWidget = QWidget()

            refCheck = QCheckBox()
            self.__refChecks.append(refCheck)
            refCheck.stateChanged.connect(self.__refBoxesChanged)
            checksLayout.addWidget(refCheck)

            adjCheck = QCheckBox()
            self.__adjChecks.append(adjCheck)
            checksLayout.addWidget(adjCheck)

            checksWidget.setLayout(checksLayout)
            self.__scrollLayout.addWidget(checksWidget, line, 2)

            line += 1

        levelAttLabel = QLabel(QCoreApplication.translate("VDLTools", "Code(s) on pipe : "))
        self.__scrollLayout.addWidget(levelAttLabel, line, 1)

        self.__levelAttCombo = QComboBox()
        self.__levelAttCombo.setMinimumHeight(20)
        self.__levelAttCombo.setMinimumWidth(50)
        self.__levelAttCombo.addItem("")
        self.__scrollLayout.addWidget(self.__levelAttCombo, line, 2)

        self.__levelAttCombo.currentIndexChanged.connect(self.__levelAttComboChanged)

        i = 0
        for layer in self.__refAvailableLayers:
            if layer in self.__refLayers:
                self.__refChecks[i].setChecked(True)
            if layer in self.__adjLayers:
                self.__adjChecks[i].setChecked(True)
            i += 1

        line += 1

        levelValLabel = QLabel(QCoreApplication.translate("VDLTools", "Point code attribute : "))
        self.__scrollLayout.addWidget(levelValLabel, line, 1)

        self.__levelValText = QLineEdit()
        if self.__levelVal is not None and self.__levelVal != "None":
            self.__levelValText.insert(self.__levelVal)
        self.__levelValText.setMinimumHeight(20)
        self.__levelValText.setMinimumWidth(100)
        self.__scrollLayout.addWidget(self.__levelValText, line, 2)

        line += 1

        drawdownLabel = QLabel(QCoreApplication.translate("VDLTools", "drawdown layer : "))
        self.__scrollLayout.addWidget(drawdownLabel, line, 1)

        self.__drawdownCombo = QComboBox()
        self.__drawdownCombo.setMinimumHeight(20)
        self.__drawdownCombo.setMinimumWidth(50)
        self.__drawdownCombo.addItem("")
        for layer in self.__drawdownLayers:
            self.__drawdownCombo.addItem(layer.name())
        self.__scrollLayout.addWidget(self.__drawdownCombo, line, 2)

        line += 1

        pipeDiamLabel = QLabel(QCoreApplication.translate("VDLTools", "Pipe diameter attribute [cm] : "))
        self.__scrollLayout.addWidget(pipeDiamLabel, line, 1)

        self.__pipeDiamCombo = QComboBox()
        self.__pipeDiamCombo.setMinimumHeight(20)
        self.__pipeDiamCombo.setMinimumWidth(50)
        self.__pipeDiamCombo.addItem("")
        self.__scrollLayout.addWidget(self.__pipeDiamCombo, line, 2)

        self.__drawdownCombo.currentIndexChanged.connect(self.__drawdownComboChanged)
        self.__pipeDiamCombo.currentIndexChanged.connect(self.__pipeDiamComboChanged)

        if self.__drawdowmLayer is not None:
            if self.__drawdowmLayer in self.__drawdownLayers:
                self.__drawdownCombo.setCurrentIndex(self.__drawdownLayers.index(self.__drawdowmLayer)+1)

        line += 1

        controlLabel = QLabel(QCoreApplication.translate("VDLTools", "Control "))
        self.__scrollLayout.addWidget(controlLabel, line, 0)

        line += 1

        controlDbLabel = QLabel(QCoreApplication.translate("VDLTools", "Control database : "))
        self.__scrollLayout.addWidget(controlDbLabel, line, 1)

        self.__controlDbCombo = QComboBox()
        self.__controlDbCombo.setMinimumHeight(20)
        self.__controlDbCombo.setMinimumWidth(50)
        self.__controlDbCombo.addItem("")
        for db in list(self.__dbs.keys()):
            self.__controlDbCombo.addItem(db)
        self.__scrollLayout.addWidget(self.__controlDbCombo, line, 2)

        line += 1

        controlSchemaLabel = QLabel(QCoreApplication.translate("VDLTools", "Control database schema : "))
        self.__scrollLayout.addWidget(controlSchemaLabel, line, 1)

        self.__controlSchemaCombo = QComboBox()
        self.__controlSchemaCombo.setMinimumHeight(20)
        self.__controlSchemaCombo.setMinimumWidth(50)
        self.__controlSchemaCombo.addItem("")
        self.__scrollLayout.addWidget(self.__controlSchemaCombo, line, 2)

        line += 1

        controlTableLabel = QLabel(QCoreApplication.translate("VDLTools", "Control config table : "))
        self.__scrollLayout.addWidget(controlTableLabel, line, 1)

        self.__controlTableCombo = QComboBox()
        self.__controlTableCombo.setMinimumHeight(20)
        self.__controlTableCombo.setMinimumWidth(50)
        self.__controlTableCombo.addItem("")
        self.__scrollLayout.addWidget(self.__controlTableCombo, line, 2)

        self.__controlDbCombo.currentIndexChanged.connect(self.__controlDbComboChanged)
        self.__controlSchemaCombo.currentIndexChanged.connect(self.__controlSchemaComboChanged)
        self.__controlTableCombo.currentIndexChanged.connect(self.__controlTableComboChanged)

        if self.__controlUriDb is not None:
            if self.__controlUriDb.database() in list(self.__dbs.keys()):
                self.__controlDbCombo.setCurrentIndex(list(self.__dbs.keys()).index(self.__controlUriDb.database()) + 1)

        if moreTools:
            line += 1

            importLabel = QLabel(QCoreApplication.translate("VDLTools", "Import "))
            self.__scrollLayout.addWidget(importLabel, line, 0)

            line += 1

            importDbLabel = QLabel(QCoreApplication.translate("VDLTools", "Import database : "))
            self.__scrollLayout.addWidget(importDbLabel, line, 1)

            self.__importDbCombo = QComboBox()
            self.__importDbCombo.setMinimumHeight(20)
            self.__importDbCombo.setMinimumWidth(50)
            self.__importDbCombo.addItem("")
            for db in list(self.__dbs.keys()):
                self.__importDbCombo.addItem(db)
            self.__scrollLayout.addWidget(self.__importDbCombo, line, 2)

            line += 1

            importSchemaLabel = QLabel(QCoreApplication.translate("VDLTools", "Import database schema : "))
            self.__scrollLayout.addWidget(importSchemaLabel, line, 1)

            self.__importSchemaCombo = QComboBox()
            self.__importSchemaCombo.setMinimumHeight(20)
            self.__importSchemaCombo.setMinimumWidth(50)
            self.__importSchemaCombo.addItem("")
            self.__scrollLayout.addWidget(self.__importSchemaCombo, line, 2)

            line += 1

            importTableLabel = QLabel(QCoreApplication.translate("VDLTools", "Import config table : "))
            self.__scrollLayout.addWidget(importTableLabel, line, 1)

            self.__importTableCombo = QComboBox()
            self.__importTableCombo.setMinimumHeight(20)
            self.__importTableCombo.setMinimumWidth(50)
            self.__importTableCombo.addItem("")
            self.__scrollLayout.addWidget(self.__importTableCombo, line, 2)

            self.__importDbCombo.currentIndexChanged.connect(self.__importDbComboChanged)
            self.__importSchemaCombo.currentIndexChanged.connect(self.__importSchemaComboChanged)
            self.__importTableCombo.currentIndexChanged.connect(self.__importTableComboChanged)

            if self.__importUriDb is not None:
                if self.__importUriDb.database() in list(self.__dbs.keys()):
                    self.__importDbCombo.setCurrentIndex(list(self.__dbs.keys()).index(self.__importUriDb.database()) + 1)

        else:
            self.__importDbCombo = None
            self.__importSchemaCombo = None
            self.__importTableCombo = None

        widget = QWidget()
        widget.setLayout(self.__scrollLayout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)

        self.__layout.addWidget(scroll, 1, 0, 1, 2)

        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools", "OK"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools", "Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout.addWidget(self.__okButton, 100, 0)
        self.__layout.addWidget(self.__cancelButton, 100, 1)
        self.setLayout(self.__layout)

    @staticmethod
    def __resetCombo(combo):
        """
        To reset a combo list
        :param combo: concerned combo
        """
        while combo.count() > 0:
            combo.removeItem(combo.count()-1)

    def __setSchemaCombo(self, uriDb, schemaCombo, schemaComboChanged, schemaDb):
        """
        To fill the schema combo list
        :param uriDb: selected database uri
        :param schemaCombo: concerned schema combo
        :param schemaComboChanged: concerned schema combo change event
        :param schemaDb: selected schema db
        """
        connector = DBConnector(uriDb, self.__iface)
        db = connector.setConnection()
        if db:
            Signal.safelyDisconnect(schemaCombo.currentIndexChanged, schemaComboChanged)
            self.__resetCombo(schemaCombo)
            schemaCombo.addItem("")
            self.__schemas = []
            query = db.exec_("""SELECT DISTINCT table_schema FROM information_schema.tables WHERE table_schema NOT IN
                ('pg_catalog', 'information_schema', 'topology') AND table_type = 'BASE TABLE' AND table_name NOT IN
                (SELECT f_table_name FROM geometry_columns)""")
            if query.lastError().isValid():
                self.__iface.messageBar().pushMessage(query.lastError().text(), level=QgsMessageBar.CRITICAL, duration=0)
            else:
                while next(query):
                    self.__schemas.append(query.value(0))
                db.close()
                for schema in self.__schemas:
                    schemaCombo.addItem(schema)
                schemaCombo.currentIndexChanged.connect(schemaComboChanged)
                if schemaDb is not None:
                    if schemaDb in self.__schemas:
                        schemaCombo.setCurrentIndex(self.__schemas.index(schemaDb) + 1)

    def __setTableCombo(self, uriDb, schema, tableCombo, tableComboChanged, configTable):
        """
        To fill the table combo list
        :param uriDb: selected database uri
        :param schema: selected database schema
        :param tableCombo: concerned table combo
        :param tableComboChanged: concerned table combo change event
        :param configTable: selected config table
        """
        connector = DBConnector(uriDb, self.__iface)
        db = connector.setConnection()
        if db:
            Signal.safelyDisconnect(tableCombo.currentIndexChanged, tableComboChanged)
            self.__resetCombo(tableCombo)
            tableCombo.addItem("")
            self.__tables = []
            query = db.exec_("""SELECT table_name FROM information_schema.tables WHERE table_schema = '""" + schema +
                             """' ORDER BY table_name""")
            if query.lastError().isValid():
                self.__iface.messageBar().pushMessage(query.lastError().text(), level=QgsMessageBar.CRITICAL, duration=0)
            else:
                while next(query):
                    self.__tables.append(query.value(0))
                db.close()
                for table in self.__tables:
                    if tableCombo.findText(table) == -1:
                        tableCombo.addItem(table)
                tableCombo.currentIndexChanged.connect(tableComboChanged)
                if configTable is not None:
                    if configTable in self.__tables:
                        tableCombo.setCurrentIndex(self.__tables.index(configTable) + 1)

    def __setPipeDiamCombo(self, drawdownLayer):
        """
        To fill the pipe diameter combo list
        :param drawdownLayer: choosen drawdown layer
        """
        Signal.safelyDisconnect(self.__pipeDiamCombo.currentIndexChanged, self.__pipeDiamComboChanged)
        self.__resetCombo(self.__pipeDiamCombo)
        self.__pipeDiamCombo.addItem("")
        fields = drawdownLayer.fields()
        self.__pipeDiamFields = []
        for field in fields:
            self.__pipeDiamFields.append(field.name())
            self.__pipeDiamCombo.addItem(field.name())
        self.__pipeDiamCombo.currentIndexChanged.connect(self.__pipeDiamComboChanged)
        if self.__pipeDiam is not None:
            if self.__pipeDiam in self.__pipeDiamFields:
                self.__pipeDiamCombo.setCurrentIndex(self.__pipeDiamFields.index(self.__pipeDiam) + 1)

    def __setLevelAttCombo(self, refLayers):
        """
        To fill the level attribute combo list
        :param refLayers: choosen reference layers
        """
        Signal.safelyDisconnect(self.__levelAttCombo.currentIndexChanged, self.__levelAttComboChanged)
        self.__resetCombo(self.__levelAttCombo)
        self.__levelAttCombo.addItem("")
        self.__levelAttFields = []
        num = 0
        for layer in refLayers:
            fields = layer.fields()
            if num == 0:
                for field in fields:
                    self.__levelAttFields.append(field.name())
                num = 1
            else:
                names = []
                for field in fields:
                    names.append(field.name())
                news = []
                for name in self.__levelAttFields:
                    if name in names:
                        news.append(name)
                self.__levelAttFields = news

        for name in self.__levelAttFields:
            self.__levelAttCombo.addItem(name)
        self.__levelAttCombo.currentIndexChanged.connect(self.__levelAttComboChanged)
        if self.__levelAtt is not None:
            if self.__levelAtt in self.__levelAttFields:
                self.__levelAttCombo.setCurrentIndex(self.__levelAttFields.index(self.__levelAtt) + 1)

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

    def __refBoxesChanged(self):
        """
        To update level attribute combo when reference layers have changed
        """
        if self.refLayers() is not None:
            self.__setLevelAttCombo(self.refLayers())

    def __drawdownComboChanged(self):
        """
        To remove blank item when another one is selected
        and update pipe diamete combo when drawdown layer has changed
        """
        if self.__drawdownCombo.itemText(0) == "":
            self.__drawdownCombo.removeItem(0)
        if self.drawdownLayer() is not None:
            self.__setPipeDiamCombo(self.drawdownLayer())

    def __controlTableComboChanged(self):
        """
        To remove blank item when another one is selected
        """
        if self.__controlTableCombo.itemText(0) == "":
            self.__controlTableCombo.removeItem(0)

    def __importTableComboChanged(self):
        """
        To remove blank item when another one is selected
        """
        if self.__importTableCombo.itemText(0) == "":
            self.__importTableCombo.removeItem(0)

    def __controlDbComboChanged(self):
        """
        When the selection in db combo has changed
        """
        if self.__controlDbCombo.itemText(0) == "":
            self.__controlDbCombo.removeItem(0)
        if self.controlUriDb() is not None:
            self.__setSchemaCombo(self.controlUriDb(), self.__controlSchemaCombo, self.__controlSchemaComboChanged,
                                  self.__controlSchemaDb)

    def __importDbComboChanged(self):
        """
        When the selection in db combo has changed
        """
        if self.__importDbCombo.itemText(0) == "":
            self.__importDbCombo.removeItem(0)
        if self.importUriDb() is not None:
            self.__setSchemaCombo(self.importUriDb(), self.__importSchemaCombo, self.__importSchemaComboChanged,
                                  self.__importSchemaDb)

    def __controlSchemaComboChanged(self):
        """
        When the selection in schema combo has changed
        """
        if self.__controlSchemaCombo.itemText(0) == "":
            self.__controlSchemaCombo.removeItem(0)
        if self.controlSchemaDb() is not None:
            self.__setTableCombo(self.controlUriDb(), self.controlSchemaDb(), self.__controlTableCombo,
                                 self.__controlTableComboChanged, self.__controlConfigTable)

    def __importSchemaComboChanged(self):
        """
        When the selection in schema combo has changed
        """
        if self.__importSchemaaCombo.itemText(0) == "":
            self.__importSchemaCombo.removeItem(0)
        if self.importSchemaDb() is not None:
            self.__setTableCombo(self.importUriDb(), self.importSchemaDb(), self.__importTableCombo,
                                 self.__importTableComboChanged, self.__importConfigTable)

    def __pipeDiamComboChanged(self):
        """
        When the selection in schema combo has changed
        """
        if self.__pipeDiamCombo.itemText(0) == "":
            self.__pipeDiamCombo.removeItem(0)

    def __levelAttComboChanged(self):
        """
        When the selection in schema combo has changed
        """
        if self.__levelAttCombo.itemText(0) == "":
            self.__levelAttCombo.removeItem(0)

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
        :return: selected memory points layer, or none
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

    def refLayers(self):
        """
        To get the selected reference layers
        :return: selected reference layers, or none
        """
        layers = []
        i = 0
        for check in self.__refChecks:
            if check.isChecked():
                layers.append(self.__refAvailableLayers[i])
            i += 1
        return layers

    def adjLayers(self):
        """
        To get the selected ajustable layers
        :return: selected adjustable layers, or none
        """
        layers = []
        i = 0
        for check in self.__adjChecks:
            if check.isChecked():
                layers.append(self.__refAvailableLayers[i])
            i += 1
        return layers

    def levelAtt(self):
        """
        To get the selected level attribute
        :return:  selected level attribute, or none
        """
        if self.__levelAttCombo is None:
            return None
        index = self.__levelAttCombo.currentIndex()
        if self.__levelAttCombo.itemText(index) == "":
            return None
        else:
            return self.__levelAttFields[index]

    def levelVal(self):
        """
        To get the filled level value
        :return: filled level value
        """
        return self.__levelValText.text()

    def drawdownLayer(self):
        """
        To get the selected drawdown layer
        :return: selected drawdown layer, or none
        """
        index = self.__drawdownCombo.currentIndex()
        if self.__drawdownCombo.itemText(index) == "":
            return None
        else:
            return self.__drawdownLayers[index]

    def pipeDiam(self):
        """
        To get the selected pipe diameter
        :return: selected pipe diameter, or none
        """
        if self.__pipeDiamCombo is None:
            return None
        index = self.__pipeDiamCombo.currentIndex()
        if self.__pipeDiamCombo.itemText(index) == "":
            return None
        else:
            return self.__pipeDiamFields[index]

    def controlConfigTable(self):
        """
        To get the selected config table
        :return: selected config table, or none
        """
        if self.__controlTableCombo is None:
            return None
        index = self.__controlTableCombo.currentIndex()
        if self.__controlTableCombo.itemText(index) == "":
            return None
        else:
            return self.__tables[index]

    def importConfigTable(self):
        """
        To get the selected config table
        :return: selected config table, or none
        """
        if self.__importTableCombo is None:
            return None
        index = self.__importTableCombo.currentIndex()
        if self.__importTableCombo.itemText(index) == "":
            return None
        else:
            return self.__tables[index]

    def controlUriDb(self):
        """
        To get selected import database uri
        :return: import database uri
        """
        if self.__controlDbCombo is None:
            return None
        index = self.__controlDbCombo.currentIndex()
        if self.__controlDbCombo.itemText(index) == "":
            return None
        else:
            return self.__dbs[list(self.__dbs.keys())[index]]

    def importUriDb(self):
        """
        To get selected import database uri
        :return: import database uri
        """
        if self.__importDbCombo is None:
            return None
        index = self.__importDbCombo.currentIndex()
        if self.__importDbCombo.itemText(index) == "":
            return None
        else:
            return self.__dbs[list(self.__dbs.keys())[index]]

    def controlSchemaDb(self):
        """
        To get selected import database schema
        :return: import database schema
        """
        if self.__controlSchemaCombo is None:
            return None
        index = self.__controlSchemaCombo.currentIndex()
        if self.__controlSchemaCombo.itemText(index) == "":
            return None
        else:
            return self.__schemas[index]

    def importSchemaDb(self):
        """
        To get selected import database schema
        :return: import database schema
        """
        if self.__importSchemaCombo is None:
            return None
        index = self.__importSchemaCombo.currentIndex()
        if self.__importSchemaCombo.itemText(index) == "":
            return None
        else:
            return self.__schemas[index]

    def mntUrl(self):
        """
        To get selected MN url
        :return: MN url
        """
        return self.__mntText.text()

