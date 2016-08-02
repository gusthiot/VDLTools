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
from qgis.core import QgsDataSourceURI
import re


class DBConnector:

    @staticmethod
    def getPrimary(layer, db):
        dataSource = QgsDataSourceURI(layer.source())
        str = """SELECT column_default FROM information_schema.columns WHERE table_name='""" + \
              dataSource.table() + """' AND column_name='""" + dataSource.keyColumn() + """'"""
        print("query", str)
        query = db.exec_(str)
        while query.next():
            return query.value(0)
        return None

    @staticmethod
    def getConnections():
        s = QSettings()
        s.beginGroup("PostgreSQL/connections")
        currentConnections = s.childGroups()
        s.endGroup()
        return currentConnections

    @staticmethod
    def setConnection(conn, iface):
        s = QSettings()
        s.beginGroup("PostgreSQL/connections/" + conn)
        db = QSqlDatabase.addDatabase('QPSQL')
        db.setHostName(s.value("host", ""))
        db.setDatabaseName(s.value("database", ""))
        db.setUserName(s.value("username", ""))
        db.setPassword(s.value("password", ""))
        s.endGroup()
        ok = db.open()
        if not ok:
            iface.messageBar().pushMessage("Database Error: " + db.lastError().text(), level=QgsMessageBar.CRITICAL)
            return None
        return db
    #
    # @staticmethod
    # def getInfos(layerInfo):
    #     if layerInfo[:6] == 'dbname':
    #         infos = {}
    #         layerInfo = layerInfo.replace('\'', '"')
    #         vals = dict(re.findall('(\S+)="?(.*?)"? ', layerInfo))
    #         infos["dbName"] = str(vals['dbname'])
    #         infos["key"] = str(vals['key'])
    #         infos["srid"] = int(vals['srid'])
    #         infos["type"] = str(vals['type'])
    #         infos["host"] = str(vals['host'])
    #         infos["port"] = int(vals['port'])
    #
    #         # need some extra processing to get table name and schema
    #         table = vals['table'].split('.')
    #         infos["schemaName"] = table[0].strip('"')
    #         infos["tableName"] = table[1].strip('"')
    #         return infos
    #     else:
    #         return None
