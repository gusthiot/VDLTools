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
from __future__ import print_function
from builtins import next
from builtins import str
from builtins import object

from qgis.gui import QgsMessageBar
from ..core.db_connector import DBConnector
from ..ui.import_jobs_dialog import ImportJobsDialog
from PyQt4.QtCore import QCoreApplication
from ..ui.import_confirm_dialog import ImportConfirmDialog
from datetime import datetime
from ..ui.import_measures_dialog import ImportMeasuresDialog


class ImportMeasures(object):
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
        self.__confDlg = None
        self.__measDlg = None
        self.__data = None
        self.__iter = 0
        self.__num = 0
        self.__job = None
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
                                    self.__configTable + """ WHERE WHERE sourcelayer_name IS NOT NULL""")
            print(query.lastError().text())
            if query.lastError().isValid():
                print(query.lastError().text())
                self.__cancel()
            else:
                while next(query):
                    if self.__sourceTable == "":
                        self.__sourceTable = query.value(0)
                    elif self.__sourceTable != query.value(0):
                        self.__iface.messageBar().pushMessage(
                            QCoreApplication.translate("VDLTools","Error"),
                            QCoreApplication.translate("VDLTools","different sources in config table ?!?"),
                            level=QgsMessageBar.WARNING)
                #  select jobs
                query = self.__db.exec_("""SELECT DISTINCT usr_session_name FROM """ + self.__sourceTable + """ WHERE
                    usr_valid = FALSE AND usr_session_name IS NOT NULL""")
                if query.lastError().isValid():
                    print(query.lastError().text())
                    self.__cancel()
                else:
                    jobs = []
                    while next(query):
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
        self.__job = self.__jobsDlg.job()
        self.__jobsDlg.accept()
        #  select geodata for insertion
        query = self.__db.exec_("""SELECT code,description,geometry,id FROM """ + self.__sourceTable +
                                """ WHERE usr_session_name = '""" + self.__job + """' AND usr_valid = FALSE""")
        if query.lastError().isValid():
            print(query.lastError().text())
        else:
            self.__data = []
            while next(query):
                data = {'code': query.value(0), 'descr': query.value(1), 'geom': query.value(2),
                        'id_survey': query.value(3)}
                # select schema and id for insertion table
                query2 = self.__db.exec_(
                    """SELECT id, schema FROM qwat_sys.doctables WHERE name = '""" + data['descr'] + """'""")
                if query2.lastError().isValid():
                    print(query2.lastError().text())
                else:
                    next(query2)
                    data['id_table'] = query2.value(0)
                    data['schema_table'] = query2.value(1)
                self.__data.append(data)
        self.__checkIfExist()

    def __checkIfExist(self):
        if self.__iter < len(self.__data):
            data = self.__data[self.__iter]

            # check if already in table
            query = self.__db.exec_(
                """SELECT ST_AsText(geometry3d) FROM """ + data['schema_table'] + """.""" + data['descr'] +
                """ WHERE st_dwithin('""" + data['geom'] + """', geometry3d, 0.03)""")
            if query.lastError().isValid():
                print(query.lastError().text())
            else:
                in_base = False
                point = None
                while next(query):
                    point = query.value(0)
                    in_base = True
                if in_base:
                    self.__data[self.__iter]['point'] = point
                    self.__confDlg = ImportConfirmDialog()
                    self.__confDlg.setMessage(
                        QCoreApplication.translate("VDLTools","There is already a " + point +
                                                   " in table " + data['schema_table'] + """.""" +
                                                   data['descr'] + ".\n Would you like to add it anyway ? "))
                    self.__confDlg.rejected.connect(self.__cancelAndNext)
                    self.__confDlg.accepted.connect(self.__confirmAndNext)
                    self.__confDlg.okButton().clicked.connect(self.__onConfirmOk)
                    self.__confDlg.cancelButton().clicked.connect(self.__onConfirmCancel)
                    self.__confDlg.show()
                else:
                    self.__confirmAndNext()
        else:
            self.__insert()

    def __onConfirmCancel(self):
        """
        When the Cancel button in Import Confirm Dialog is pushed
        """
        self.__confDlg.reject()

    def __onConfirmOk(self):
        """
        When the Ok button in Import Confirm Dialog is pushed
        """
        self.__confDlg.accept()

    def __cancelAndNext(self):
        self.__data[self.__iter]['add'] = False
        self.__nextCheck()

    def __confirmAndNext(self):
        self.__data[self.__iter]['add'] = True
        self.__nextCheck()

    def __nextCheck(self):
        self.__iter += 1
        self.__checkIfExist()

    def __insert(self):
        not_added = []
        for data in self.__data:
            if data['add']:
                destLayer = ""
                request = """INSERT INTO """ + data['schema_table'] + """.""" + data['descr']
                columns = "(id,geometry3d"
                values = "(nextval('" + data['schema_table'] + """.""" + data['descr'] + "_id_seq'::regclass),'" + \
                         data['geom'] + "'"

                #  select import data for insertion
                query = self.__db.exec_(
                    """SELECT destinationlayer_name,destinationcolumn_name,static_value FROM """ +
                    self.__schemaDb + """.""" + self.__configTable + """ WHERE code = '""" + data['code'] +
                    """' AND static_value IS NOT NULL""")
                if query.lastError().isValid():
                    print(query.lastError().text())
                else:
                    while next(query):
                        if destLayer == "":
                            destLayer = query.value(0)
                        elif destLayer != query.value(0):
                            self.__iface.messageBar().pushMessage(
                                QCoreApplication.translate("VDLTools","Error"),
                                QCoreApplication.translate("VDLTools",
                                                           "different destination layer in config table ?!?"),
                                level=QgsMessageBar.WARNING)
                        columns += "," + query.value(1)
                        values += "," + query.value(2)
                    columns += ")"
                    values += ")"
                    request += " " + columns + """ VALUES """ + values + """ RETURNING id"""
                    #  insert data
                    query2 = self.__db.exec_(request)
                    if query2.lastError().isValid():
                        print(query2.lastError().text())
                    else:
                        self.__num += 1
                        query2.first()
                        id_object = query2.value(0)
                        # update source table
                        query3 = self.__db.exec_("""UPDATE """ + self.__sourceTable + """ SET usr_valid_date = '""" +
                            str(datetime.date(datetime.now())) + """', usr_valid = TRUE""" +
                            """, usr_fk_network_element = """ + str(id_object) + """, usr_fk_table = """ +
                            str(data['id_table']) + """, usr_import_user = '""" + self.__db.userName() +
                            """' WHERE id = """ + str(data['id_survey']))
                        if query3.lastError().isValid():
                            print(query3.lastError().text())
            else:
                not_added.append(data)
        if len(not_added) > 0:
            self.__measDlg = ImportMeasuresDialog(not_added, self.__job)
            self.__measDlg.rejected.connect(self.__validAndNext)
            self.__measDlg.accepted.connect(self.__deleteAndNext)
            self.__measDlg.okButton().clicked.connect(self.__onDeleteOk)
            self.__measDlg.cancelButton().clicked.connect(self.__onDeleteCancel)
            self.__measDlg.show()
        else:
            self.__conclude()

    def __conclude(self):
        if self.__num > 0:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "Success"),
                QCoreApplication.translate("VDLTools", str(self.__num) + " points inserted !"),level=QgsMessageBar.INFO)
        self.__cancel()

    def __onDeleteCancel(self):
        """
        When the Cancel button in Import Measures Dialog is pushed
        """
        self.__measDlg.reject()

    def __onDeleteOk(self):
        """
        When the Ok button in Import Measures Dialog is pushed
        """
        self.__measDlg.accept()

    def __ids(self):
        pos = 0
        ids = ""
        for data in self.__measDlg.data():
            if pos == 0:
                pos += 1
            else:
                ids += ","
            ids += str(data['id_survey'])
        return ids

    def __validAndNext(self):
        query = self.__db.exec_("""UPDATE """ + self.__sourceTable + """ SET usr_valid_date = '""" +
                                str(datetime.date(datetime.now())) + """', usr_valid = TRUE""" +
                                """, usr_import_user = '""" + self.__db.userName() +
                                """' WHERE id IN (""" + self.__ids() + """)""")
        if query.lastError().isValid():
            print(query.lastError().text())
        self.__conclude()

    def __deleteAndNext(self):
        query = self.__db.exec_("""DELETE FROM """ + self.__sourceTable +
                                """ WHERE id IN (""" + self.__ids() + """)""")
        if query.lastError().isValid():
            print(query.lastError().text())
        self.__conclude()

    def __cancel(self):
        self.__confDlg = None
        self.__jobsDlg = None
        self.__measDlg = None
        self.__data = None
        self.__iter = 0
        self.__num = 0
        self.__db.close()

    def __onCancel(self):
        """
        When the Cancel button in Import Jobs Dialog is pushed
        """
        self.__jobsDlg.reject()




