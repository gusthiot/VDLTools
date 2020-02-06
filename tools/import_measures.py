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
from future.builtins import next
from future.builtins import str
from future.builtins import object

from qgis.gui import QgsMessageBar
from qgis.core import QgsMapLayer,QgsDataSourceURI
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
        self.icon_path = ':/plugins/VDLTools/icons/import_icon.png'
        self.text = QCoreApplication.translate("VDLTools", "Import Measures")
        self.ownSettings = None
        self.__configTable = None
        self.__schemaDb = None
        self.__db = None
        self.__jobsDlg = None
        self.__confDlg = None
        self.__measDlg = None
        self.__data = None
        self.__iter = 0
        self.__num = 0
        self.__jobs = None
        self.__sourceTable = ""
        self.__selectedFeatures = None

    def start(self):
        """
        To start the importation
        """
        if self.ownSettings is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "No settings given !!"),
                                                  level=QgsMessageBar.CRITICAL, duration=0)
            return
        if self.ownSettings.importUriDb is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "No import db given !!"),
                                                  level=QgsMessageBar.CRITICAL, duration=0)
            return
        if self.ownSettings.importSchemaDb is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "No import db schema given !!"),
                                                  level=QgsMessageBar.CRITICAL, duration=0)
            return
        if self.ownSettings.importConfigTable is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "No import config table given !!"),
                                                  level=QgsMessageBar.CRITICAL, duration=0)
            return
        self.__configTable = self.ownSettings.importConfigTable
        self.__schemaDb = self.ownSettings.importSchemaDb

        self.__connector = DBConnector(self.ownSettings.importUriDb, self.__iface)
        self.__db = self.__connector.setConnection()
        if self.__db is not None:
            query = self.__db.exec_("""SELECT DISTINCT sourcelayer_name FROM %s.%s WHERE sourcelayer_name IS NOT NULL"""
                                    % (self.__schemaDb, self.__configTable))
            if query.lastError().isValid():
                self.__iface.messageBar().pushMessage(
                    query.lastError().text(), level=QgsMessageBar.CRITICAL, duration=0)
                self.__cancel()
            else:
                while next(query):
                    if self.__sourceTable == "":
                        self.__sourceTable = query.value(0)
                    elif self.__sourceTable != query.value(0):
                        self.__iface.messageBar().pushMessage(
                            QCoreApplication.translate("VDLTools", "different sources in config table ?!?"),
                            level=QgsMessageBar.WARNING)
                for layer in self.__iface.mapCanvas().layers():
                    if layer is not None and layer.type() == QgsMapLayer.VectorLayer and \
                                    layer.providerType() == "postgres":
                        uri = QgsDataSourceURI(layer.source())
                        if self.__sourceTable == uri.schema() + "." + uri.table():
                            self.__selectedFeatures = []
                            for f in layer.selectedFeatures():
                                self.__selectedFeatures.append(f.attribute("ID"))
                            break

                #  select jobs
                query = self.__db.exec_(("""SELECT DISTINCT usr_session_name FROM %s WHERE """ % self.__sourceTable) +
                                        """usr_valid = FALSE AND usr_session_name IS NOT NULL""")
                if query.lastError().isValid():
                    self.__iface.messageBar().pushMessage(
                        query.lastError().text(), level=QgsMessageBar.CRITICAL, duration=0)
                    self.__cancel()
                else:
                    jobs = []
                    while next(query):
                        jobs.append(query.value(0))
                    if len(jobs) == 0 and (self.__selectedFeatures is None or len(self.__selectedFeatures) == 0):
                        self.__cancel()
                    else:
                        selected = True
                        if self.__selectedFeatures is None or len(self.__selectedFeatures) == 0:
                            selected = False
                        self.__jobsDlg = ImportJobsDialog(jobs, selected)
                        self.__jobsDlg.jobsRadio().clicked.connect(self.__onJobsRadio)
                        if self.__jobsDlg.pointsRadio() is not None:
                            self.__jobsDlg.pointsRadio().clicked.connect(self.__onPointsRadio)
                        self.__jobsDlg.rejected.connect(self.__cancel)
                        self.__jobsDlg.okButton().clicked.connect(self.__onOk)
                        self.__jobsDlg.cancelButton().clicked.connect(self.__onCancel)
                        self.__jobsDlg.show()

    def __onPointsRadio(self):
        """
        When the Points Radio Button in Import Jobs Dialog is selected
        """
        self.__jobsDlg.enableJobs(False)

    def __onJobsRadio(self):
        """
        When the Jobs Radio Button in Import Jobs Dialog is selected
        """
        self.__jobsDlg.enableJobs(True)

    def __onOk(self):
        """
        When the Ok button in Import Jobs Dialog is pushed
        """
        self.__jobsDlg.accept()

        codes = []
        query = self.__db.exec_("""SELECT DISTINCT code FROM %s.%s""" % (self.__schemaDb, self.__configTable))
        if query.lastError().isValid():
            self.__iface.messageBar().pushMessage(query.lastError().text(), level=QgsMessageBar.CRITICAL, duration=0)
            self.__cancel()
        else:
            while next(query):
                codes.append(query.value(0))

            if self.__jobsDlg.jobsRadio().isChecked():
                self.__jobs = self.__jobsDlg.jobs()
                #  select geodata for insertion
                jobs = ""
                i = 0
                for job in self.__jobs:
                    if i == 0:
                        i += 1
                    else:
                        jobs += ","
                    jobs += "'" + job + "'"
                condition = """usr_session_name IN (""" + jobs + """)"""
            else:
                ids = ""
                i = 0
                for selected in self.__selectedFeatures:
                    if i == 0:
                        i += 1
                    else:
                        ids += ","
                    ids += "'" + str(selected) + "'"
                condition = """id IN (""" + ids + """)"""
            query = self.__db.exec_("""SELECT code,usr_fk_table,geometry,id,usr_session_name FROM %s WHERE %s AND 
                usr_valid = FALSE""" % (self.__sourceTable, condition))
            if query.lastError().isValid():
                self.__iface.messageBar().pushMessage(
                    query.lastError().text(), level=QgsMessageBar.CRITICAL, duration=0)
            else:
                self.__data = []
                while next(query):
                    code = int(query.value(0))
                    if code in codes:
                        data = {'code': code, 'id_table': query.value(1), 'geom': query.value(2),
                                'id_survey': query.value(3), 'job': query.value(4)}
                        # select schema and id for insertion table
                        query2 = self.__db.exec_("""SELECT schema, name FROM qwat_sys.doctables WHERE id = %s"""
                                                 % str(data['id_table']))
                        if query2.lastError().isValid():
                            self.__iface.messageBar().pushMessage(
                                query2.lastError().text(), level=QgsMessageBar.CRITICAL, duration=0)
                        else:
                            next(query2)
                            data['schema_table'] = query2.value(0)
                            data['name_table'] = query2.value(1)
                        self.__data.append(data)
                    else:
                        self.__iface.messageBar().pushMessage(
                            QCoreApplication.translate("VDLTools", "Code not in config table, measure not processed"),
                            level=QgsMessageBar.CRITICAL, duration=0)
                self.__checkIfExist()

    def __checkIfExist(self):
        """
        To check if the data we want to import is already in the table
        """
        if self.__iter < len(self.__data):
            data = self.__data[self.__iter]

            # check if already in table
            query = self.__db.exec_(
                """SELECT ST_AsText(geometry3d) FROM %s.%s WHERE st_dwithin('%s', geometry3d, 0.03)"""
                % (data['schema_table'], data['name_table'],data['geom']))
            if query.lastError().isValid():
                self.__iface.messageBar().pushMessage(
                    query.lastError().text(), level=QgsMessageBar.CRITICAL, duration=0)
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
                        QCoreApplication.translate("VDLTools", "There is already a ") + point +
                                                   QCoreApplication.translate("VDLTools", " in table ") + data['schema_table'] + """.""" +
                                                   data['name_table'] + ".\n" + QCoreApplication.translate("VDLTools", "Would you like to add it anyway ? "))
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
        """
        To flag we will not import this data and check the next
        """
        self.__data[self.__iter]['add'] = False
        self.__nextCheck()

    def __confirmAndNext(self):
        """
        To flag we will import this data and check the next
        """
        self.__data[self.__iter]['add'] = True
        self.__nextCheck()

    def __nextCheck(self):
        """
        To check the next data
        :return:
        """
        self.__iter += 1
        self.__checkIfExist()

    def __insert(self):
        """
        To insert the data into the tables
        """
        not_added = []
        for data in self.__data:
            if data['add']:
                destLayer = ""
                request = """INSERT INTO %s.%s""" % (data['schema_table'], data['name_table'])
                columns = "(id,geometry3d"
                values = """(nextval('%s.%s_id_seq'::regclass),'%s'""" \
                         % (data['schema_table'], data['name_table'], data['geom'])

                #  select import data for insertion
                query = self.__db.exec_("""SELECT destinationlayer_name,destinationcolumn_name,static_value FROM """ +
                                        """"%s.%s WHERE code = '%s' AND static_value IS NOT NULL"""
                                        % (self.__schemaDb, self.__configTable, str(data['code'])))
                if query.lastError().isValid():
                    self.__iface.messageBar().pushMessage(
                        query.lastError().text(), level=QgsMessageBar.CRITICAL, duration=0)
                else:
                    while next(query):
                        if destLayer == "":
                            destLayer = query.value(0)
                        elif destLayer != query.value(0):
                            self.__iface.messageBar().pushMessage(
                                QCoreApplication.translate("VDLTools",
                                                           "different destination layer in config table ?!?"),
                                level=QgsMessageBar.WARNING)
                        columns += "," + query.value(1)
                        values += "," + query.value(2)
                    columns += ")"
                    values += ")"
                    request += """ %s VALUES %s RETURNING id""" % (columns, values)
                    #  insert data
                    query2 = self.__db.exec_(request)
                    if query2.lastError().isValid():
                        self.__iface.messageBar().pushMessage(
                            query2.lastError().text(), level=QgsMessageBar.CRITICAL, duration=0)
                    else:
                        self.__num += 1
                        query2.first()
                        id_object = query2.value(0)
                        # update source table
                        query3 = self.__db.exec_(
                            ("""UPDATE %s SET usr_valid_date = '%s', usr_valid = TRUE, usr_fk_network_element = %s,"""
                             % (self.__sourceTable, str(datetime.date(datetime.now())), str(id_object))) +
                            (""" usr_fk_table = %s, usr_import_user = '%s' WHERE id = %s"""
                            % (str(data['id_table']), self.__db.userName(), str(data['id_survey']))))
                        if query3.lastError().isValid():
                            self.__iface.messageBar().pushMessage(query3.lastError().text(),
                                                                  level=QgsMessageBar.CRITICAL, duration=0)
            else:
                not_added.append(data)
        if len(not_added) > 0:
            self.__measDlg = ImportMeasuresDialog(not_added)
            self.__measDlg.rejected.connect(self.__validAndNext)
            self.__measDlg.accepted.connect(self.__deleteAndNext)
            self.__measDlg.okButton().clicked.connect(self.__onDeleteOk)
            self.__measDlg.cancelButton().clicked.connect(self.__onDeleteCancel)
            self.__measDlg.show()
        else:
            self.__conclude()

    def __conclude(self):
        """
        To display a resume message and clear variables
        """
        if self.__num > 0:
            self.__iface.messageBar().pushMessage(
                str(self.__num) + QCoreApplication.translate("VDLTools", " points inserted !"),level=QgsMessageBar.INFO)
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
        """
        To create string data list
        :return: string list
        """
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
        """
        To update data in source table and conclude
        """
        query = self.__db.exec_(
            """UPDATE %s SET usr_valid_date = '%s', usr_valid = TRUE, usr_import_user = '%s' WHERE id IN (%s)"""
            % (self.__sourceTable, str(datetime.date(datetime.now())), self.__db.userName(), self.__ids()))
        if query.lastError().isValid():
            self.__iface.messageBar().pushMessage(query.lastError().text(), level=QgsMessageBar.CRITICAL, duration=0)
        self.__conclude()

    def __deleteAndNext(self):
        """
        To delete data in source table and conclude
        """
        query = self.__db.exec_("""DELETE FROM %s WHERE id IN (%s)""" % (self.__sourceTable, self.__ids()))
        if query.lastError().isValid():
            self.__iface.messageBar().pushMessage(query.lastError().text(), level=QgsMessageBar.CRITICAL, duration=0)
        self.__conclude()

    def __cancel(self):
        """
        To cancel used variables
        """
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




