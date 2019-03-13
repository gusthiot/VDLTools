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
from builtins import str
from builtins import range

from ..ui.show_settings_dialog import ShowSettingsDialog
from ..ui.fields_settings_dialog import FieldsSettingsDialog
from qgis.PyQt.QtCore import (QCoreApplication,
                              QObject,
                              pyqtSignal,
                              QVariant)
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import (QgsProject,
                       QgsWkbTypes,
                       edit,
                       QgsField,
                       QgsMapLayer)
from ..core.db_connector import DBConnector
from ..core.geometry_v2 import GeometryV2


class ShowSettings(QObject):
    """
    Class to manage plugin settings
    """

    changedSignal = pyqtSignal()

    def __init__(self, iface, moreTools):
        """
        Constructor
        :param iface: interface
        """
        QObject.__init__(self)
        self.__iface = iface
        self.icon_path = ':/plugins/VDLTools/icons/settings_icon.png'
        self.text = QCoreApplication.translate("VDLTools", "Settings")
        self.__showDlg = None
        self.__ctlDb = None
        self.__configTable = None
        self.__uriDb = None
        self.__schemaDb = None
        self.__memoryPointsLayer = None
        self.__memoryLinesLayer = None
        self.__refLayers = []
        self.__adjLayers = []
        self.__levelAtt = None
        self.__levelVals = []
        self.__drawdownLayer = None
        self.__pipeDiam = None
        self.__mntUrl = None
        self.__project_loaded()
        QgsProject.instance().readProject.connect(self.__project_loaded)
        self.__linesLayer = None
        self.__fieldnames = None
        self.__moreTools = moreTools

    def __project_loaded(self):
        """
        Get saved settings on load
        """

        """ Reference point layers for drawdown tool """
        str_ids = QgsProject.instance().readEntry("VDLTools", "ref_layers", "None")[0]
        ref_ids = str_ids.split(',')

        """ Adjustable point layers for drawdown tool """
        str_ids = QgsProject.instance().readEntry("VDLTools", "adj_layers", "None")[0]
        adj_ids = str_ids.split(',')

        """ Level attribute for drawdown tool """
        self.__levelAtt = QgsProject.instance().readEntry("VDLTools", "level_att", "None")[0]

        """ Level value for drawdown tool """
        value = QgsProject.instance().readEntry("VDLTools", "level_val", "None")[0]
        self.__levelVals = value.split(",")

        """ Drawdown line layer """
        dd_id = QgsProject.instance().readEntry("VDLTools", "drawdown_layer", "None")[0]

        """ Pipe diameter attribute for drawdown line layer """
        self.__pipeDiam = QgsProject.instance().readEntry("VDLTools", "pipe_diam", "None")[0]

        """ Url used to get mnt values on a line """
        self.__mntUrl = QgsProject.instance().readEntry("VDLTools", "mnt_url", "None")[0]

        """ Config table in Database for importing new Lausanne data """
        self.__configTable = QgsProject.instance().readEntry("VDLTools", "config_table", None)[0]

        """ Database used for importing new Lausanne data """
        dbName = QgsProject.instance().readEntry("VDLTools", "db_name", None)[0]

        """ Table in Database containing control values for importing new Lausanne data """
        ctlDbName = QgsProject.instance().readEntry("VDLTools", "ctl_db_name", None)[0]

        """ Schema of the Database used for importing new Lausanne data """
        self.__schemaDb = QgsProject.instance().readEntry("VDLTools", "schema_db", None)[0]

        """ Temporarly points layer for the project """
        mpl_id = QgsProject.instance().readEntry("VDLTools", "memory_points_layer", None)[0]

        """ Temporarly lines layer for the project """
        mll_id = QgsProject.instance().readEntry("VDLTools", "memory_lines_layer", None)[0]

        for layer in list(QgsProject.instance().mapLayers().values()):
            if layer and layer.type() == QgsMapLayer.VectorLayer:
                if layer.providerType() == "memory":
                    if layer.geometryType() == QgsWkbTypes.PointGeometry:
                        if layer.id() == mpl_id:
                            self.__memoryPointsLayer = layer
                    if layer.geometryType() == QgsWkbTypes.LineGeometry:
                        if layer.id() == mll_id:
                            self.__memoryLinesLayer = layer
                if GeometryV2.getAdaptedWKB(layer.wkbType()) == QgsWkbTypes.LineStringZ:
                        if layer.id() == dd_id:
                            self.__drawdownLayer = layer
                if GeometryV2.getAdaptedWKB(layer.wkbType()) == QgsWkbTypes.PointZ:
                        if layer.id() in ref_ids:
                            self.__refLayers.append(layer)
                        if layer.id() in adj_ids:
                            self.__adjLayers.append(layer)

        if dbName != "":
            usedDbs = DBConnector.getUsedDatabases()
            if dbName in list(usedDbs.keys()):
                self.__uriDb = usedDbs[dbName]
        if ctlDbName != "":
            usedDbs = DBConnector.getUsedDatabases()
            if ctlDbName in list(usedDbs.keys()):
                self.__ctlDb = usedDbs[ctlDbName]

        self.changedSignal.emit()

    def start(self):
        """
        To start the show settings, meaning display a Show Settings Dialog
        """
        levelVal = ','.join(str(x) for x in self.__levelVals)
        self.__showDlg = ShowSettingsDialog(self.__iface, self.__memoryPointsLayer, self.__memoryLinesLayer,
                                            self.__ctlDb, self.__configTable, self.__uriDb, self.__schemaDb,
                                            self.__mntUrl, self.__refLayers, self.__adjLayers, self.__levelAtt,
                                            levelVal, self.__drawdownLayer, self.__pipeDiam, self.__moreTools)
        self.__showDlg.okButton().clicked.connect(self.__onOk)
        self.__showDlg.cancelButton().clicked.connect(self.__onCancel)
        self.__showDlg.show()

    def __onOk(self):
        """
        When the Ok button in Show Settings Dialog is pushed
        """
        values = self.__showDlg.levelVal().split(',')
        for v in values:
            if not v.isdigit():
                QMessageBox.information(
                    None, QCoreApplication.translate("VDLTools", "Error"),
                    QCoreApplication.translate("VDLTools", "Point code attribute has to be numbers separated by comma")
                )
                return

        self.__showDlg.accept()
        self.linesLayer = self.__showDlg.linesLayer()
        self.pointsLayer = self.__showDlg.pointsLayer()
        self.configTable = self.__showDlg.configTable()
        self.uriDb = self.__showDlg.uriDb()
        self.ctlDb = self.__showDlg.ctlDb()
        self.schemaDb = self.__showDlg.schemaDb()
        self.mntUrl = self.__showDlg.mntUrl()
        self.refLayers = self.__showDlg.refLayers()
        self.adjLayers = self.__showDlg.adjLayers()
        self.levelAtt = self.__showDlg.levelAtt()
        self.levelVals = self.__showDlg.levelVal()
        self.drawdownLayer = self.__showDlg.drawdownLayer()
        self.pipeDiam = self.__showDlg.pipeDiam()
        self.changedSignal.emit()

    def __onCancel(self):
        """
        When the Cancel button in Show Settings Dialog is pushed
        """
        self.__showDlg.reject()

    def __memoryLinesLayerDeleted(self):
        """
        To delete the saved memory lines layer
        """
        self.__memoryLinesLayer = None
        QgsProject.instance().writeEntry("VDLTools", "memory_lines_layer", None)

    def __memoryPointsLayerDeleted(self):
        """
        To delete the saved memory points layer
        """
        self.__memoryPointsLayer = None
        QgsProject.instance().writeEntry("VDLTools", "memory_points_layer", None)

    def __drawdownLayerDeleted(self):
        """
        To delete the saved drawdown layer
        """
        self.__drawdownLayer = None
        QgsProject.instance().writeEntry("VDLTools", "drawdown_layer", None)

    @property
    def pointsLayer(self):
        """
        To get the saved memory points layer
        :return: saved memory points layer
        """
        return self.__memoryPointsLayer

    @property
    def linesLayer(self):
        """
        To get the saved memory lines layer
        :return: saved memory lines layer
        """
        return self.__memoryLinesLayer

    @property
    def configTable(self):
        """
        To get the saved config table (for import tool)
        :return: saved config table
        """
        return self.__configTable

    @property
    def mntUrl(self):
        """
        To get the saved mnt url
        :return: saved mnt url
        """
        return self.__mntUrl

    @property
    def refLayers(self):
        """
        To get the saved reference layers
        :return: saved reference layers
        """
        return self.__refLayers

    @property
    def adjLayers(self):
        """
        To get the saved adjustable layers
        :return: saved adjustable layers
        """
        return self.__adjLayers

    @property
    def levelAtt(self):
        """
        To get the saved level attribute
        :return: saved level attribute
        """
        return self.__levelAtt

    @property
    def levelVals(self):
        """
        To get the saved level value
        :return: saved level value
        """
        return self.__levelVals

    @property
    def drawdownLayer(self):
        """
        To get the saved drawdown layer
        :return: saved drawdown layer
        """
        return self.__drawdownLayer

    @property
    def pipeDiam(self):
        """
        To get the saved pipe diameter
        :return: saved pipe diameter
        """
        return self.__pipeDiam

    @property
    def uriDb(self):
        """
        To get the saved uri import database
        :return: saved uri import database
        """
        return self.__uriDb

    @property
    def ctlDb(self):
        """
        To get the saved uri control database
        :return: saved uri control database
        """
        return self.__ctlDb

    @property
    def schemaDb(self):
        """
        To get the saved schema import database
        :return: saved schema import database
        """
        return self.__schemaDb

    @pointsLayer.setter
    def pointsLayer(self, pointsLayer):
        """
        To set the saved memory points layer
        :param pointsLayer: memory points layer to save
        """
        self.__memoryPointsLayer = pointsLayer
        layer_id = None
        if pointsLayer:
            layer_id = pointsLayer.id()
            self.__memoryPointsLayer.destroyed.connect(self.__memoryPointsLayerDeleted)
        QgsProject.instance().writeEntry("VDLTools", "memory_points_layer", layer_id)

    @linesLayer.setter
    def linesLayer(self, linesLayer):
        """
        To set the saved memory lines layer, but first check layer fields
        :param linesLayer: memory lines layer to save
        """
        self.__linesLayer = linesLayer
        if linesLayer:
            fields = self.__linesLayer.fields()
            fieldsNames = []
            for pos in range(fields.count()):
                fieldsNames.append(fields.at(pos).name())
            if "distance" not in fieldsNames or "x" not in fieldsNames or "y" not in fieldsNames:
                self.__fieldnames = fieldsNames
                self.__fieldsDlg = FieldsSettingsDialog()
                self.__fieldsDlg.rejected.connect(self.__cancel)
                self.__fieldsDlg.okButton().clicked.connect(self.__onFieldsOk)
                self.__fieldsDlg.butButton().clicked.connect(self.__onFieldsBut)
                self.__fieldsDlg.cancelButton().clicked.connect(self.__onFieldsCancel)
                self.__fieldsDlg.show()
            else:
                self.reallySetLinesLayer()

    def __onFieldsCancel(self):
        """
        When the Cancel button in Fields Settings Dialog is pushed
        """
        self.__fieldsDlg.reject()

    def __cancel(self):
        """
        To cancel used variables
        """
        self.__linesLayer = None

    def __onFieldsOk(self):
        """
        When the Ok button in Fields Settings Dialog is pushed
        """
        self.__fieldsDlg.accept()
        with edit(self.__linesLayer):
            if "distance" not in self.__fieldnames:
                self.__linesLayer.addAttribute(QgsField("distance", QVariant.Double))
            if "x" not in self.__fieldnames:
                self.__linesLayer.addAttribute(QgsField("x", QVariant.Double))
            if "y" not in self.__fieldnames:
                self.__linesLayer.addAttribute(QgsField("y", QVariant.Double))
            self.reallySetLinesLayer()

    def __onFieldsBut(self):
        """
        When the Without Fields button in Fields Settings Dialog is pushed
        """
        self.__fieldsDlg.accept()
        self.reallySetLinesLayer()

    def reallySetLinesLayer(self):
        """
        To really set the saved memory lines layer, with parametrized fields
        """
        self.__memoryLinesLayer = self.__linesLayer
        layer_id = None
        if self.__linesLayer:
            layer_id = self.__linesLayer.id()
            self.__memoryLinesLayer.destroyed.connect(self.__memoryLinesLayerDeleted)
        QgsProject.instance().writeEntry("VDLTools", "memory_lines_layer", layer_id)
        self.__cancel()

    @configTable.setter
    def configTable(self, configTable):
        """
        To set the saved config table
        :param configTable: config table to save
        """
        self.__configTable = configTable
        if configTable is not None:
            QgsProject.instance().writeEntry("VDLTools", "config_table", configTable)

    @mntUrl.setter
    def mntUrl(self, mntUrl):
        """
        To set the saved mnt url
        :param mntUrl: saved mnt url
        """
        self.__mntUrl = mntUrl
        if mntUrl is not None:
            QgsProject.instance().writeEntry("VDLTools", "mnt_url", mntUrl)

    @refLayers.setter
    def refLayers(self, refLayers):
        """
        To set the saved reference layers
        :param refLayers: saved reference layers
        """
        self.__refLayers = refLayers
        ids = ""
        for layer in refLayers:
            if layer:
                if ids != "":
                    ids += ","
                ids += str(layer.id())
                # layer.destroyed.connect(self.__refLayerDeleted)
        QgsProject.instance().writeEntry("VDLTools", "ref_layers", ids)

    @adjLayers.setter
    def adjLayers(self, adjLayers):
        """
        To set the saved adjustable layers
        :param adjLayers: saved adjustable layers
        """
        self.__adjLayers = adjLayers
        ids = ""
        for layer in adjLayers:
            if layer:
                if ids != "":
                    ids += ","
                ids += str(layer.id())
        QgsProject.instance().writeEntry("VDLTools", "adj_layers", ids)

    @levelAtt.setter
    def levelAtt(self, levelAtt):
        """
        To set the saved level attribute
        :param levelAtt: saved level attribute
        """
        self.__levelAtt = levelAtt
        if levelAtt is not None:
            QgsProject.instance().writeEntry("VDLTools", "level_att", levelAtt)

    @levelVals.setter
    def levelVals(self, levelVals):
        """
        To set the saved level values
        :param levelVals: saved level values
        """
        self.__levelVals = levelVals.split(",")
        if levelVals is not None:
            QgsProject.instance().writeEntry("VDLTools", "level_val", levelVals)

    @drawdownLayer.setter
    def drawdownLayer(self, drawdownLayer):
        """
        To set the saved drawdown layer
        :param drawdownLayer: saved drawdown layer
        """
        self.__drawdownLayer = drawdownLayer
        layer_id = None
        if drawdownLayer:
            layer_id = drawdownLayer.id()
            self.__drawdownLayer.destroyed.connect(self.__drawdownLayerDeleted)
        QgsProject.instance().writeEntry("VDLTools", "drawdown_layer", layer_id)

    @pipeDiam.setter
    def pipeDiam(self, pipeDiam):
        """
        To set the saved pipe diameter
        :param pipeDiam: saved pipe diameter
        """
        self.__pipeDiam = pipeDiam
        if pipeDiam is not None:
            QgsProject.instance().writeEntry("VDLTools", "pipe_diam", pipeDiam)

    @uriDb.setter
    def uriDb(self, uriDb):
        """
        To set the saved uri import database
        :param uriDb: saved uri import database
        """
        self.__uriDb = uriDb
        if uriDb is not None:
            QgsProject.instance().writeEntry("VDLTools", "db_name", uriDb.database())

    @ctlDb.setter
    def ctlDb(self, ctlDb):
        """
        To set the saved uri control database
        :param ctlDb: saved uri control database
        """
        self.__ctlDb = ctlDb
        if ctlDb is not None:
            QgsProject.instance().writeEntry("VDLTools", "ctl_db_name", ctlDb.database())

    @schemaDb.setter
    def schemaDb(self, schemaDb):
        """
        To set the saved schema import database
        :param schemaDb: saved schema import database
        """
        self.__schemaDb = schemaDb
        if schemaDb is not None:
            QgsProject.instance().writeEntry("VDLTools", "schema_db", schemaDb)
