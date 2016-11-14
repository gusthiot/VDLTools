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
from PyQt4.QtCore import QCoreApplication
from datetime import datetime


class ImportMeasures:
    """
    Class to import measurements data into given tables
    """

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        self.__iface = iface
        self.__icon_path = ':/plugins/VDLTools/icons/import_icon.png'
        self.__text = QCoreApplication.translate("VDLTools","Import Measures")
        self.__ownSettings = None
        self.__configTable = None
        self.__uriDb = None
        self.__schemaDb = None
        self.__db = None
        self.__jobsDlg = None
        self.__sourceTable = ""

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

    def start(self):
        """
        To start the importation
        """
        if self.__ownSettings is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools","Error"),
                                                  QCoreApplication.translate("VDLTools","No settings given !!"),
                                                  level=QgsMessageBar.CRITICAL)
            return
        if self.__ownSettings.uriDb() is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools","Error"),
                                                  QCoreApplication.translate("VDLTools","No import db given !!"),
                                                  level=QgsMessageBar.CRITICAL)
            return
        if self.__ownSettings.schemaDb() is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools","Error"),
                                                  QCoreApplication.translate("VDLTools","No db schema given !!"),
                                                  level=QgsMessageBar.CRITICAL)
            return
        if self.__ownSettings.configTable() is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools","Error"),
                                                  QCoreApplication.translate("VDLTools","No config table given !!"),
                                                  level=QgsMessageBar.CRITICAL)
            return
        self.__configTable = self.__ownSettings.configTable()
        self.__schemaDb = self.__ownSettings.schemaDb()
        self.__uriDb = self.__ownSettings.uriDb()

        self.__connector = DBConnector(self.__uriDb, self.__iface)
        self.__db = self.__connector.setConnection()
        if self.__db is not None:
            query = self.__db.exec_("""SELECT DISTINCT sourcelayer_name FROM """ + self.__schemaDb + """.""" +
                                    self.__configTable + """ WHERE sourcelayer_name IS NOT NULL""")
            if query.lastError().isValid():
                print query.lastError().text()
                self.__cancel()
            else:
                while query.next():
                    if self.__sourceTable == "":
                        self.__sourceTable = query.value(0)
                    elif self.__sourceTable != query.value(0):
                        self.__iface.messageBar().pushMessage(
                            QCoreApplication.translate("VDLTools","Error"),
                            QCoreApplication.translate("VDLTools","different sources in config table ?!?"),
                            level=QgsMessageBar.WARNING)
                query = self.__db.exec_("""SELECT DISTINCT usr_session_name FROM """ + self.__sourceTable + """ WHERE
                    usr_valid = FALSE""")
                if query.lastError().isValid():
                    print query.lastError().text()
                    self.__cancel()
                else:
                    jobs = []
                    while query.next():
                        jobs.append(query.value(0))

                    self.__jobsDlg = ImportJobsDialog(jobs)
                    self.__jobsDlg.rejected.connect(self.__cancel)
                    self.__jobsDlg.okButton().clicked.connect(self.__onOk)
                    self.__jobsDlg.cancelButton().clicked.connect(self.__onCancel)
                    self.__jobsDlg.show()

    def __onOk(self):
        """
        When the Ok button in Import Jobs Dialog is pushed
        """
        job = self.__jobsDlg.job()
        self.__jobsDlg.accept()
        query = self.__db.exec_("""SELECT code,description,geometry,id FROM """ + self.__sourceTable +
                                """ WHERE usr_session_name = '""" + job + """'""")
        if query.lastError().isValid():
            print query.lastError().text()
        else:
            while query.next():
                code = query.value(0)
                descr = query.value(1)
                geom = query.value(2)
                id_survey = query.value(3)
                query2 = self.__db.exec_(
                    """SELECT id, schema FROM qwat_sys.doctables WHERE name = '""" + descr + """'""")
                if query2.lastError().isValid():
                    print query2.lastError().text()
                else:
                    query2.next()
                    id_table = query2.value(0)
                    schema_table = query2.value(1)
                    destLayer = ""
                    request = """INSERT INTO """ + schema_table + """.""" + descr
                    columns = "(id,geometry3d"
                    values = "(nextval('" + schema_table + """.""" + descr + "_id_seq'::regclass),'" + geom + "'"
                    query2 = self.__db.exec_(
                        """SELECT destinationlayer_name,destinationcolumn_name,static_value FROM """ +
                        self.__schemaDb + """.""" + self.__configTable + """ WHERE code = '""" + code +
                        """' AND static_value IS NOT NULL""")
                    if query2.lastError().isValid():
                        print query2.lastError().text()
                    else:
                        while query2.next():
                            if destLayer == "":
                                destLayer = query2.value(0)
                            elif destLayer != query2.value(0):
                                self.__iface.messageBar().pushMessage(
                                    QCoreApplication.translate("VDLTools","Error"),
                                    QCoreApplication.translate("VDLTools",
                                                               "different destination layer in config table ?!?"),
                                    level=QgsMessageBar.WARNING)
                            columns += "," + query2.value(1)
                            values += ",'" + query2.value(2) + "'"
                        columns += ")"
                        values += ")"
                        request += " " + columns + """ VALUES """ + values + """ RETURNING id"""
                        query2 = self.__db.exec_(request)
                        if query2.lastError().isValid():
                            print query2.lastError().text()
                        else:
                            query2.first()
                            id_object = query2.value(0)
                            query3 = self.__db.exec_(
                                """UPDATE """ + self.__sourceTable + """ SET usr_valid_date = '""" +
                                str(datetime.date(datetime.now())) + """', usr_valid = TRUE""" +
                                """', usr_fk_network_element = '""" + id_object + """', usr_fk_table = '""" +
                                id_table + """', usr_import_user = '""" + self.__db.userName() + """' WHERE id = '""" +
                                id_survey + """'""")
                            if query3.lastError().isValid():
                                print query3.lastError().text()
                            else:
                                print "ok"
        self.__cancel()

    def __cancel(self):
        self.__db.close()

    def __onCancel(self):
        """
        When the Cancel button in Import Jobs Dialog is pushed
        """
        self.__jobsDlg.reject()




