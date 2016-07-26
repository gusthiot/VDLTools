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

from qgis.gui import QgsMessageBar
from ..core.db_connector import DBConnector
from ..ui.import_jobs_dialog import ImportJobsDialog


class ImportMeasures:

    def __init__(self, iface):
        self.__iface = iface
        self.__icon_path = ':/plugins/VDLTools/icons/import_icon.png'
        self.__text = 'Import Measures'
        self.__ownSettings = None
        self.__configTable = None
        self.__db = None
        self.__jobsDlg = None
        self.__sourceTable = ""

    def icon_path(self):
        return self.__icon_path

    def text(self):
        return self.__text

    def setOwnSettings(self, settings):
        self.__ownSettings = settings

    def start(self):
        if self.__ownSettings is None:
            self.__iface.messageBar().pushMessage("Error", "No settings are given !!",
                                                  level=QgsMessageBar.CRITICAL, duration=5)
            return
        if self.__ownSettings.configTable() is None:
            self.__iface.messageBar().pushMessage("Error", "No config table is given !!",
                                                  level=QgsMessageBar.CRITICAL, duration=5)
            return
        self.__configTable = self.__ownSettings.configTable()

        conn = DBConnector.getConnections()
        self.__db = DBConnector.setConnection(conn[0], self.__iface)
        query = self.__db.exec_("""SELECT DISTINCT source FROM """ + self.__configTable + """ WHERE source NOT NULL""")
        while query.next():
            if self.__sourceTable == "":
                self.__sourceTable = query.value(0)
            elif self.__sourceTable != query.value(0):
                self.__iface.messageBar().pushMessage("Error", "different sources in config table ?!?",
                                                      level=QgsMessageBar.WARNING, duration=5)
        query = self.__db.exec_("""SELECT DISTINCT job FROM """ + self.__sourceTable + """ WHERE
            traitement = 'non-traité'""")
        jobs = []
        while query.next():
            jobs.append(query.value(0))

        self.__jobsDlg = ImportJobsDialog(jobs)
        self.__jobsDlg.okButton().clicked.connect(self.__onOk)
        self.__jobsDlg.cancelButton().clicked.connect(self.__onCancel)
        self.__jobsDlg.show()

    def __onOk(self):
        job = self.__jobsDlg.job()
        self.__jobsDlg.close()
        self.__jobsDlg.okButton().clicked.disconnect(self.__onOk)
        self.__jobsDlg.cancelButton().clicked.disconnect(self.__onCancel)
        query = self.__db.exec_("""SELECT 1,2,3 FROM """ + self.__sourceTable + """ WHERE job = '""" + job + """'""")
        while query.next():
            pass



    def __onCancel(self):
        self.__jobsDlg.close()
        self.__jobsDlg.okButton().clicked.disconnect(self.__onOk)
        self.__jobsDlg.cancelButton().clicked.disconnect(self.__onCancel)
        self.__db.close()




