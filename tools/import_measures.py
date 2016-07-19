# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-07-19
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

from ..core.db_connector import DBConnector


class ImportMeasures:

    def __init__(self, iface):
        self.__iface = iface
        self.__icon_path = ':/plugins/VDLTools/icons/import_icon.png'
        self.__text = 'Import Measures'
        self.__ownSettings = None
        self.__configTable = None

    def icon_path(self):
        return self.__icon_path

    def text(self):
        return self.__text

    def setOwnSettings(self, settings):
        self.__ownSettings = settings

    def start(self):
        if self.__ownSettings is None:
            print "No settings are given !!"
        if self.__ownSettings.configTable() is None:
            print "No config table is given !!"
        self.__configTable = self.__ownSettings.configTable()

        conn = DBConnector.getConnections()
        db = DBConnector.setConnection(conn[0])
        query = db.exec_("""SELECT DISTINCT source FROM """ + self.__configTable + """ WHERE source NOT NULL""")
        sourceTable = ""
        while query.next():
            if sourceTable == "":
                sourceTable = query.value(0)
            elif sourceTable != query.value(0):
                print "different source ?!?"
        query = db.exec_("""SELECT DISTINCT job FROM """ + sourceTable + """ WHERE traitement = 'non-traité'""")
        jobs = []
        while query.next():
            jobs.append(query.value(0))

        db.close()

