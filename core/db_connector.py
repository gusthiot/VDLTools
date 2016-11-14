# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-07-18
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

from PyQt4.QtCore import QSettings
from PyQt4.QtSql import QSqlDatabase
from qgis.gui import QgsMessageBar
from PyQt4.QtCore import QCoreApplication
from qgis.core import (QgsMapLayer,
                       QgsCredentials,
                       QgsMapLayerRegistry,
                       QgsDataSourceURI)

class DBConnector:
    """
    Class to manage database connection
    """

    def __init__(self, uri, iface):
        self.__dbName = uri.database()
        self.__host = uri.host()
        self.__username = uri.username()
        self.__pwd = uri.password()
        self.__port = uri.port()
        self.__iface = iface

        s = QSettings()
        s.beginGroup("PostgreSQL/connections")
        connections = s.childGroups()
        s.endGroup()
        for connection in connections:
            s.beginGroup("PostgreSQL/connections/" + connection)
            if s.value("database", "") == self.__dbName:
                if self.__host is None:
                    if s.value("host", "") != "":
                        self.__host = s.value("host", "")
                if self.__username is None:
                    if s.value("username", "") != "":
                        self.__username = s.value("username", "")
                if self.__pwd is None:
                    if s.value("password", "") != "":
                        self.__pwd = s.value("password", "")
                if self.__port is None:
                    if s.value("port", "") != "":
                        self.__port = s.value("port", "")
                s.endGroup()
                break
            s.endGroup()

        if self.__username == "" or self.__pwd == "":
            (success, user, passwd) = QgsCredentials.instance().get(uri.connectionInfo(), self.__username, self.__pwd)
            if success:
                QgsCredentials.instance().put(uri.connectionInfo(), user, passwd)
                self.__username = user
                self.__pwd = passwd

    def setConnection(self):
        db = QSqlDatabase.addDatabase('QPSQL')
        db.setHostName(self.__host)
        db.setDatabaseName(self.__dbName)
        db.setUserName(self.__username)
        db.setPassword(self.__pwd)
        db.setPort(int(self.__port))
        ok = db.open()
        if not ok:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "Database Error: ") + db.lastError().text(),
                level=QgsMessageBar.CRITICAL)
            return None
        return db

    @staticmethod
    def getUsedDatabases():
        dbs = {}
        for layer in QgsMapLayerRegistry.instance().mapLayers().values():
            if layer is not None and layer.type() == QgsMapLayer.VectorLayer and layer.providerType() == "postgres":
                uri = QgsDataSourceURI(layer.source())
                if uri.database() not in dbs:
                    dbs[uri.database()] = uri
        print dbs.keys()
        return dbs
