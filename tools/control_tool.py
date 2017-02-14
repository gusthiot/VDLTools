# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2017-02-14
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
from __future__ import division
from PyQt4.QtCore import QCoreApplication
from .area_tool import AreaTool
from ..ui.choose_control_dialog import ChooseControlDialog
from qgis.gui import QgsMessageBar
from qgis.core import QgsMapLayerRegistry,QgsVectorLayer,QgsGeometry,QgsFeature
from ..core.db_connector import DBConnector


class ControlTool(AreaTool):
    """
    Map tool class to make control request
    """

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        AreaTool.__init__(self, iface)
        self.__iface = iface
        self.__icon_path = ':/plugins/VDLTools/icons/control_icon.png'
        self.__text = QCoreApplication.translate("VDLTools","Make control requests on selected area")
        self.releasedSignal.connect(self.__released)
        self.__chooseDlg = None
        self.__db = None
        self.__ownSettings = None
        self.__requests = {
            "nom1": self.__request1,
            "nom2": self.__request2
        }
        self.__crs = self.__iface.mapCanvas().mapSettings().destinationCrs().postgisSrid()

    def icon_path(self):
        """
        To get the icon path
        :return: icon path
        """
        return self.__icon_path

    def text(self):
        """
        To get the menu text
        :return: menu text
        """
        return self.__text

    def setOwnSettings(self, settings):
        """
        To set the settings
        :param settings: income settings
        """
        self.__ownSettings = settings

    def toolName(self):
        """
        To get the tool name
        :return: tool name
        """
        return QCoreApplication.translate("VDLTools","Control")

    def setTool(self):
        """
        To set the current tool as this one
        """
        self.canvas().setMapTool(self)

    def __released(self):
        if self.__ownSettings is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools","Error"),
                                                  QCoreApplication.translate("VDLTools","No settings given !!"),
                                                  level=QgsMessageBar.CRITICAL)
            return
        if self.__ownSettings.ctlDb() is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools","Error"),
                                                  QCoreApplication.translate("VDLTools","No control db given !!"),
                                                  level=QgsMessageBar.CRITICAL)
            return

        self.__chooseDlg = ChooseControlDialog(self.__requests.keys())
        self.__chooseDlg.okButton().clicked.connect(self.__onOk)
        self.__chooseDlg.cancelButton().clicked.connect(self.__onCancel)
        self.__chooseDlg.show()

    def __onCancel(self):
        self.__chooseDlg.reject()

    def __onOk(self):
        self.__chooseDlg.accept()

        self.__connector = DBConnector(self.__ownSettings.ctlDb(), self.__iface)
        self.__db = self.__connector.setConnection()

        if self.__db is not None:
            for name in self.__chooseDlg.controls():
                self.__requests[name]()
            self.__cancel()

    def __request1(self):
        layer_name = "request1"
        fNames = ["id"]
        fTypes = ["int"]
        query = self.__db.exec_("""SELECT GeometryType(geometry3d), ST_AsText(geometry3d), id FROM qwat_od.pipe WHERE ST_Intersects(geometry3d,ST_GeomFromText('""" +
                                self.geom().exportToWkt() + """',""" + str(self.__crs) + """))""")
        if query.lastError().isValid():
            print(query.lastError().text())
        else:
            gtype = None
            geometries = []
            attributes = []
            while query.next():
                gtype = query.value(0)
                geometries.append(query.value(1))
                attributes.append([query.value(2)])
            print(len(geometries))

            self.__createMemoryLayer(layer_name, gtype, geometries, attributes, fNames, fTypes)

    def __request2(self):
        query = self.__db.exec_("""SELECT id, GeometryType(geometry3d) FROM qwat_od.valve WHERE ST_Intersects(geometry3d,ST_GeomFromText('""" +
                                self.geom().exportToWkt() + """',""" + str(self.__crs) + """))""")
        if query.lastError().isValid():
            print(query.lastError().text())
        else:
            nb = 0
            while query.next():
                nb += 1

    def __createMemoryLayer(self, layer_name, gtype, geometries, attributes, fNames, fTypes):
            layerList = QgsMapLayerRegistry.instance().mapLayersByName(layer_name)
            if layerList:
                QgsMapLayerRegistry.instance().removeMapLayers([layerList[0].id()])
            epsg = self.canvas().mapRenderer().destinationCrs().authid()
            fieldsParam = ""
            for i in range(len(fNames)):
                fieldsParam += "&field=" + fNames[i] + ":" + fTypes[i]
            layer = QgsVectorLayer(gtype + "?crs=" + epsg + fieldsParam + "&index=yes", layer_name, "memory")
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            layer.startEditing()
            for i in range(len(geometries)):
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry().fromWkt(geometries[i]))
                fields = layer.pendingFields()
                feature.setFields(fields)
                for j in range(len(fNames)):
                    feature.setAttribute(fNames[j], attributes[i][j])
                layer.addFeature(feature)
            layer.commitChanges()

    def __cancel(self):
        self.__chooseDlg = None
        self.__db.close()
