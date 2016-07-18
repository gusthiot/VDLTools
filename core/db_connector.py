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


class DBConnector:

    @staticmethod
    def getLastPrimaryValue(primary, layer):
        values = layer.getValues(primary)
        print("values", values[0])
        last = 0
        for val in values[0]:
            if val > last:
                last = val
        print("last", last)
        return last

    @staticmethod
    def getPrimaryField(layer):
        conn = DBConnector.getConnections()
        db = DBConnector.setConnection(conn[0])
        if not db:
            return None
        primary = db.primaryIndex(layer.name())
        print("record", db.record(layer.name()).value(primary.fieldName(0)))
        if primary.count() == 0:
            print("no primary key ?!?")
            return None
        for i in xrange(primary.count()):
            print("record " + str(i), primary.fieldName(i))
        return primary.fieldName(0)

    @staticmethod
    def getConnections():
        s = QSettings()
        s.beginGroup("PostgreSQL/connections")
        currentConnections = s.childGroups()
        s.endGroup()
        return currentConnections

    @staticmethod
    def setConnection(conn):
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
            print("Database Error: %s" % db.lastError().text())
            return None
        return db
