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

    def __init__(self, iface, memoryPointsLayer, memoryLinesLayer, ctllDb, configTable, uriDb, schemaDb, mntUrl,
                 refLayers, adjLayers, levelAtt, levelVal, drawdowmLayer, pipeDiam, moreTools):
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
        self.__ctlDb = ctllDb
        self.__configTable = configTable
        self.__uriDb = uriDb
        self.__schemaDb = schemaDb
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

       # self.resize(450, 400)
        self.__layout = QGridLayout()

        line = 0

        intersectLabel = QLabel(QCoreApplication.translate("VDLTools", "Intersect "))
        self.__layout.addWidget(intersectLabel, line, 0)

        line += 1

        pointLabel = QLabel(QCoreApplication.translate("VDLTools", "Working points layer : "))
        self.__layout.addWidget(pointLabel, line, 1)

        self.__pointCombo = QComboBox()
        self.__pointCombo.setMinimumHeight(20)
        self.__pointCombo.setMinimumWidth(50)
        self.__pointCombo.addItem("")
        for layer in self.__pointsLayers:
            self.__pointCombo.addItem(layer.name())
        self.__layout.addWidget(self.__pointCombo, line, 2)
        self.__pointCombo.currentIndexChanged.connect(self.__pointComboChanged)
        if self.__memoryPointsLayer is not None:
            if self.__memoryPointsLayer in self.__pointsLayers:
                self.__pointCombo.setCurrentIndex(self.__pointsLayers.index(self.__memoryPointsLayer)+1)

        line += 1

        lineLabel = QLabel(QCoreApplication.translate("VDLTools", "Working lines layer : "))
        self.__layout.addWidget(lineLabel, line, 1)

        self.__lineCombo = QComboBox()
        self.__lineCombo.setMinimumHeight(20)
        self.__lineCombo.setMinimumWidth(50)
        self.__lineCombo.addItem("")
        for layer in self.__linesLayers:
            self.__lineCombo.addItem(layer.name())
        self.__layout.addWidget(self.__lineCombo, line, 2)
        self.__lineCombo.currentIndexChanged.connect(self.__lineComboChanged)
        if self.__memoryLinesLayer is not None:
            if self.__memoryLinesLayer in self.__linesLayers:
                self.__lineCombo.setCurrentIndex(self.__linesLayers.index(self.__memoryLinesLayer)+1)

        line += 1

        profilesLabel = QLabel(QCoreApplication.translate("VDLTools", "Profiles "))
        self.__layout.addWidget(profilesLabel, line, 0)

        line += 1

        mntLabel = QLabel(QCoreApplication.translate("VDLTools", "Url for MNT : "))
        self.__layout.addWidget(mntLabel, line, 1)

        self.__mntText = QLineEdit()
        if self.__mntUrl is None or self.__mntUrl == "None":
            self.__mntText.insert('http://map.lausanne.ch/main/wsgi/profile.json')
        else:
            self.__mntText.insert(self.__mntUrl)
        self.__mntText.setMinimumHeight(20)
        self.__mntText.setMinimumWidth(100)
        self.__layout.addWidget(self.__mntText, line, 2)

        line += 1

        ddLabel = QLabel(QCoreApplication.translate("VDLTools", "Drawdown "))
        self.__layout.addWidget(ddLabel, line, 0)

        line += 1

        self.__layout.addWidget(QLabel(QCoreApplication.translate("VDLTools", "Layer")), line, 1)

        namesLayout = QHBoxLayout()
        namesWidget = QWidget()
        namesLayout.addWidget(QLabel(QCoreApplication.translate("VDLTools", "Reference")))
        namesLayout.addWidget(QLabel(QCoreApplication.translate("VDLTools", "Adjustable")))
        namesLayout.setContentsMargins(0,0,0,0)
        namesWidget.setLayout(namesLayout)
        self.__layout.addWidget(namesWidget, line, 2)

        line += 1

        for layer in self.__refAvailableLayers:
            refLabel = QLabel("  - " + layer.name())
            self.__refLabels.append(refLabel)
            self.__layout.addWidget(refLabel, line, 1)

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
            self.__layout.addWidget(checksWidget, line, 2)

            line += 1

        levelAttLabel = QLabel(QCoreApplication.translate("VDLTools", "Code(s) on pipe : "))
        self.__layout.addWidget(levelAttLabel, line, 1)

        self.__levelAttCombo = QComboBox()
        self.__levelAttCombo.setMinimumHeight(20)
        self.__levelAttCombo.setMinimumWidth(50)
        self.__levelAttCombo.addItem("")
        self.__layout.addWidget(self.__levelAttCombo, line, 2)

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
        self.__layout.addWidget(levelValLabel, line, 1)

        self.__levelValText = QLineEdit()
        if self.__levelVal is not None and self.__levelVal != "None":
            self.__levelValText.insert(self.__levelVal)
        self.__levelValText.setMinimumHeight(20)
        self.__levelValText.setMinimumWidth(100)
        self.__layout.addWidget(self.__levelValText, line, 2)

        line += 1

        drawdownLabel = QLabel(QCoreApplication.translate("VDLTools", "drawdown layer : "))
        self.__layout.addWidget(drawdownLabel, line, 1)

        self.__drawdownCombo = QComboBox()
        self.__drawdownCombo.setMinimumHeight(20)
        self.__drawdownCombo.setMinimumWidth(50)
        self.__drawdownCombo.addItem("")
        for layer in self.__drawdownLayers:
            self.__drawdownCombo.addItem(layer.name())
        self.__layout.addWidget(self.__drawdownCombo, line, 2)

        line += 1

        pipeDiamLabel = QLabel(QCoreApplication.translate("VDLTools", "Pipe diameter attribute [cm] : "))
        self.__layout.addWidget(pipeDiamLabel, line, 1)

        self.__pipeDiamCombo = QComboBox()
        self.__pipeDiamCombo.setMinimumHeight(20)
        self.__pipeDiamCombo.setMinimumWidth(50)
        self.__pipeDiamCombo.addItem("")
        self.__layout.addWidget(self.__pipeDiamCombo, line, 2)

        self.__drawdownCombo.currentIndexChanged.connect(self.__drawdownComboChanged)
        self.__pipeDiamCombo.currentIndexChanged.connect(self.__pipeDiamComboChanged)

        if self.__drawdowmLayer is not None:
            if self.__drawdowmLayer in self.__drawdownLayers:
                self.__drawdownCombo.setCurrentIndex(self.__drawdownLayers.index(self.__drawdowmLayer)+1)

        if moreTools:
            line += 1

            importLabel = QLabel(QCoreApplication.translate("VDLTools", "Import "))
            self.__layout.addWidget(importLabel, line, 0)

            line += 1

            dbLabel = QLabel(QCoreApplication.translate("VDLTools", "Import database : "))
            self.__layout.addWidget(dbLabel, line, 1)

            self.__dbCombo = QComboBox()
            self.__dbCombo.setMinimumHeight(20)
            self.__dbCombo.setMinimumWidth(50)
            self.__dbCombo.addItem("")
            for db in list(self.__dbs.keys()):
                self.__dbCombo.addItem(db)
            self.__layout.addWidget(self.__dbCombo, line, 2)

            line += 1

            schemaLabel = QLabel(QCoreApplication.translate("VDLTools", "Database schema : "))
            self.__layout.addWidget(schemaLabel, line, 1)

            self.__schemaCombo = QComboBox()
            self.__schemaCombo.setMinimumHeight(20)
            self.__schemaCombo.setMinimumWidth(50)
            self.__schemaCombo.addItem("")
            self.__layout.addWidget(self.__schemaCombo, line, 2)

            line += 1

            tableLabel = QLabel(QCoreApplication.translate("VDLTools", "Config table : "))
            self.__layout.addWidget(tableLabel, line, 1)

            self.__tableCombo = QComboBox()
            self.__tableCombo.setMinimumHeight(20)
            self.__tableCombo.setMinimumWidth(50)
            self.__tableCombo.addItem("")
            self.__layout.addWidget(self.__tableCombo, line, 2)

            line += 1

            controlLabel = QLabel(QCoreApplication.translate("VDLTools", "Control "))
            self.__layout.addWidget(controlLabel, line, 0)

            line += 1

            ctlLabel = QLabel(QCoreApplication.translate("VDLTools", "Control database : "))
            self.__layout.addWidget(ctlLabel, line, 1)

            self.__ctlCombo = QComboBox()
            self.__ctlCombo.setMinimumHeight(20)
            self.__ctlCombo.setMinimumWidth(50)
            self.__ctlCombo.addItem("")
            for db in list(self.__dbs.keys()):
                self.__ctlCombo.addItem(db)
            self.__layout.addWidget(self.__ctlCombo, line, 2)

            self.__dbCombo.currentIndexChanged.connect(self.__dbComboChanged)
            self.__schemaCombo.currentIndexChanged.connect(self.__schemaComboChanged)
            self.__tableCombo.currentIndexChanged.connect(self.__tableComboChanged)

            self.__ctlCombo.currentIndexChanged.connect(self.__ctlComboChanged)

            if self.__uriDb is not None:
                if self.__uriDb.database() in list(self.__dbs.keys()):
                    self.__dbCombo.setCurrentIndex(list(self.__dbs.keys()).index(self.__uriDb.database()) + 1)

            if self.__ctlDb is not None:
                if self.__ctlDb.database() in list(self.__dbs.keys()):
                    self.__ctlCombo.setCurrentIndex(list(self.__dbs.keys()).index(self.__ctlDb.database()) + 1)
        else:
            self.__dbCombo = None
            self.__schemaCombo = None
            self.__tableCombo = None
            self.__ctlCombo = None

        self.__okButton = QPushButton(QCoreApplication.translate("VDLTools", "OK"))
        self.__okButton.setMinimumHeight(20)
        self.__okButton.setMinimumWidth(100)

        self.__cancelButton = QPushButton(QCoreApplication.translate("VDLTools", "Cancel"))
        self.__cancelButton.setMinimumHeight(20)
        self.__cancelButton.setMinimumWidth(100)

        self.__layout.addWidget(self.__okButton, 100, 1)
        self.__layout.addWidget(self.__cancelButton, 100, 2)
        self.setLayout(self.__layout)

    @staticmethod
    def __resetCombo(combo):
        """
        To reset a combo list
        :param combo: concerned combo
        """
        while combo.count() > 0:
            combo.removeItem(combo.count()-1)

    def __setSchemaCombo(self, uriDb):
        """
        To fill the schema combo list
        :param uriDb: selected database uri
        """
        connector = DBConnector(uriDb, self.__iface)
        db = connector.setConnection()
        if db:
            Signal.safelyDisconnect(self.__schemaCombo.currentIndexChanged, self.__schemaComboChanged)
            self.__resetCombo(self.__schemaCombo)
            self.__schemaCombo.addItem("")
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
                    self.__schemaCombo.addItem(schema)
                self.__schemaCombo.currentIndexChanged.connect(self.__schemaComboChanged)
                if self.__schemaDb is not None:
                    if self.__schemaDb in self.__schemas:
                        self.__schemaCombo.setCurrentIndex(self.__schemas.index(self.__schemaDb) + 1)

    def __setTableCombo(self, uriDb, schema):
        """
        To fill the table combo list
        :param uriDb: selected database uri
        :param schema: selected database schema
        """
        connector = DBConnector(uriDb, self.__iface)
        db = connector.setConnection()
        if db:
            Signal.safelyDisconnect(self.__tableCombo.currentIndexChanged, self.__tableComboChanged)
            self.__resetCombo(self.__tableCombo)
            self.__tableCombo.addItem("")
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
                    if self.__tableCombo.findText(table) == -1:
                        self.__tableCombo.addItem(table)
                self.__tableCombo.currentIndexChanged.connect(self.__tableComboChanged)
                if self.__configTable is not None:
                    if self.__configTable in self.__tables:
                        self.__tableCombo.setCurrentIndex(self.__tables.index(self.__configTable) + 1)

    def __setPipeDiamCombo(self, drawdownLayer):
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
        if self.refLayers() is not None:
            self.__setLevelAttCombo(self.refLayers())

    def __drawdownComboChanged(self):
        """
        To remove blank item when another one is selected
        """
        if self.__drawdownCombo.itemText(0) == "":
            self.__drawdownCombo.removeItem(0)
        if self.drawdownLayer() is not None:
            self.__setPipeDiamCombo(self.drawdownLayer())

    def __tableComboChanged(self):
        """
        To remove blank item when another one is selected
        """
        if self.__tableCombo.itemText(0) == "":
            self.__tableCombo.removeItem(0)

    def __dbComboChanged(self):
        """
        When the selection in db combo has changed
        """
        if self.__dbCombo.itemText(0) == "":
            self.__dbCombo.removeItem(0)
        if self.uriDb() is not None:
            self.__setSchemaCombo(self.uriDb())

    def __schemaComboChanged(self):
        """
        When the selection in schema combo has changed
        """
        if self.__schemaCombo.itemText(0) == "":
            self.__schemaCombo.removeItem(0)
        if self.schemaDb() is not None:
            self.__setTableCombo(self.uriDb(), self.schemaDb())

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

    def __ctlComboChanged(self):
        """
        When the selection in ctl combo has changed
        """
        if self.__ctlCombo.itemText(0) == "":
            self.__ctlCombo.removeItem(0)

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
        if self.__levelAttCombo is None:
            return None
        index = self.__levelAttCombo.currentIndex()
        if self.__levelAttCombo.itemText(index) == "":
            return None
        else:
            return self.__levelAttFields[index]

    def levelVal(self):
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
        if self.__pipeDiamCombo is None:
            return None
        index = self.__pipeDiamCombo.currentIndex()
        if self.__pipeDiamCombo.itemText(index) == "":
            return None
        else:
            return self.__pipeDiamFields[index]

    def configTable(self):
        """
        To get the selected config table
        :return: selected config table, or none
        """
        if self.__tableCombo is None:
            return None
        index = self.__tableCombo.currentIndex()
        if self.__tableCombo.itemText(index) == "":
            return None
        else:
            return self.__tables[index]

    def uriDb(self):
        """
        To get selected import database uri
        :return: import database uri
        """
        if self.__dbCombo is None:
            return None
        index = self.__dbCombo.currentIndex()
        if self.__dbCombo.itemText(index) == "":
            return None
        else:
            return self.__dbs[list(self.__dbs.keys())[index]]

    def schemaDb(self):
        """
        To get selected import database schema
        :return: import database schema
        """
        if self.__schemaCombo is None:
            return None
        index = self.__schemaCombo.currentIndex()
        if self.__schemaCombo.itemText(index) == "":
            return None
        else:
            return self.__schemas[index]

    def mntUrl(self):
        """
        To get selected MN url
        :return: MN url
        """
        return self.__mntText.text()

    def ctlDb(self):
        """
        To get selected control database uri
        :return: control database uri
        """
        if self.__ctlCombo is None:
            return None
        index = self.__ctlCombo.currentIndex()
        if self.__ctlCombo.itemText(index) == "":
            return None
        else:
            return self.__dbs[list(self.__dbs.keys())[index]]
