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
from builtins import str
from builtins import range
from qgis.PyQt.QtCore import QCoreApplication
from .area_tool import AreaTool
from ..ui.choose_control_dialog import ChooseControlDialog
from qgis.core import (QgsProject,
                       Qgis,
                       QgsVectorLayer,
                       QgsGeometry,
                       QgsFeature)
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
        self.icon_path = ':/plugins/VDLTools/icons/control_icon.png'
        self.text = QCoreApplication.translate("VDLTools", "Make control requests on selected area")
        self.releasedSignal.connect(self.__released)
        self.__chooseDlg = None
        self.__db = None
        self.ownSettings = None
        self.__requests = {
            "nom1": self.__request1
        }
        self.__crs = None

    def toolName(self):
        """
        To get the tool name
        :return: tool name
        """
        return QCoreApplication.translate("VDLTools", "Control")

    def setTool(self):
        """
        To set the current tool as this one
        """
        self.canvas().setMapTool(self)

    def __released(self):
        """
        When selection is complete
        """
        if self.ownSettings is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "No settings given !!"),
                                                  level=Qgis.Critical, duration=0)
            return
        if self.ownSettings.ctlDb is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "No control db given !!"),
                                                  level=Qgis.Critical, duration=0)
            return

        self.__chooseDlg = ChooseControlDialog(list(self.__requests.keys()))
        self.__chooseDlg.okButton().clicked.connect(self.__onOk)
        self.__chooseDlg.cancelButton().clicked.connect(self.__onCancel)
        self.__chooseDlg.show()

    def __onCancel(self):
        """
        When the Cancel button in Choose Control Dialog is pushed
        """
        self.__chooseDlg.reject()

    def __onOk(self):
        """
        When the Ok button in Choose Control Dialog is pushed
        """
        self.__chooseDlg.accept()

        self.__connector = DBConnector(self.ownSettings.ctlDb, self.__iface)
        self.__db = self.__connector.setConnection()

        if self.__db is not None:
            for name in self.__chooseDlg.controls():
                self.__requests[name]()
            self.__cancel()

    def __request1(self):
        """
        Request which can be choosed for control
        """
        self.__crs = self.canvas().mapSettings().destinationCrs().postgisSrid()
        layer_name = "request1"
        fNames = ["id", "fk_status"]
        select_part = """SELECT GeometryType(geometry3d), ST_AsText(geometry3d)"""
        for f in fNames:
            select_part += """, %s, pg_typeof(%s)""" % (f, f)
        from_part = """ FROM qwat_od.pipe """
        where_part = """WHERE ST_Intersects(geometry3d,ST_GeomFromText('%s',%s))""" \
                     % (self.geom().asWkt(), str(self.__crs))
        request = select_part + from_part + where_part
        print(request)
        self.__querying(request, layer_name, fNames)

    def __querying(self, request, layer_name, fNames):
        """
        Process query to database and display the results
        :param request: request string to query
        :param layer_name: name for new memory layer to display the results
        :param fNames: fields names requested as result
        """
        query = self.__db.exec_(request)
        if query.lastError().isValid():
            self.__iface.messageBar().pushMessage(query.lastError().text(), level=Qgis.Critical, duration=0)
        else:
            gtype = None
            geometries = []
            attributes = []
            fTypes = []
            while next(query):
                gtype = query.value(0)
                geometries.append(query.value(1))
                atts = []
                for i in range(len(fNames)):
                    atts.append(query.value(2*i+2))
                    fTypes.append(query.value(2*i+3))
                attributes.append(atts)
            print(len(geometries))
            if len(geometries) > 0:
                self.__createMemoryLayer(layer_name, gtype, geometries, attributes, fNames, fTypes)

    def __createMemoryLayer(self, layer_name, gtype, geometries, attributes, fNames, fTypes):
        """
        Create a memory layer from parameters
        :param layer_name: name for the layer
        :param gtype: geometry type of the layer
        :param geometries: objects geometries
        :param attributes: objects attributes
        :param fNames: fields names
        :param fTypes: fields types
        """
        layerList = QgsProject.instance().mapLayersByName(layer_name)
        if layerList:
            QgsProject.instance().removeMapLayers([layerList[0].id()])
        epsg = self.canvas().mapRenderer().destinationCrs().authid()
        fieldsParam = ""
        for i in range(len(fNames)):
            fieldsParam += "&field=" + fNames[i] + ":" + fTypes[i]
        layer = QgsVectorLayer(gtype + "?crs=" + epsg + fieldsParam + "&index=yes", layer_name, "memory")
        QgsProject.instance().addMapLayer(layer)
        layer.startEditing()
        for i in range(len(geometries)):
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry().fromWkt(geometries[i]))
            feature.setFields(layer.fields())
            for j in range(len(fNames)):
                feature.setAttribute(fNames[j], attributes[i][j])
            layer.addFeature(feature)
        layer.commitChanges()

    def __cancel(self):
        """
        To cancel used variables
        """
        self.__chooseDlg = None
        self.__db.close()
