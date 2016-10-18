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
from qgis.core import QgsDataSourceURI
from ..core.db_connector import DBConnector
from ..ui.import_jobs_dialog import ImportJobsDialog
from PyQt4.QtCore import QCoreApplication


class ImportMeasures:
    """
    Class to import measurments data into given tables
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
        if self.__ownSettings.configTable() is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools","Error"),
                                                  QCoreApplication.translate("VDLTools","No config table given !!"),
                                                  level=QgsMessageBar.CRITICAL)
            return
        self.__configTable = self.__ownSettings.configTable()

        dataSource = QgsDataSourceURI(self.__layer.source())
        self.__db = DBConnector.setConnection(dataSource.database(), self.__iface)
        if self.__db:
            query = self.__db.exec_("""SELECT DISTINCT source FROM """ + self.__configTable +
                                    """ WHERE source NOT NULL""")
            while query.next():
                if self.__sourceTable == "":
                    self.__sourceTable = query.value(0)
                elif self.__sourceTable != query.value(0):
                    self.__iface.messageBar().pushMessage(
                        QCoreApplication.translate("VDLTools","Error"),
                        QCoreApplication.translate("VDLTools","different sources in config table ?!?"),
                        level=QgsMessageBar.WARNING)
            query = self.__db.exec_("""SELECT DISTINCT job FROM """ + self.__sourceTable + """ WHERE
                traitement = 'non-traité'""")
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
        query = self.__db.exec_("""SELECT 1,2,3 FROM """ + self.__sourceTable + """ WHERE job = '""" + job + """'""")
        while query.next():
            pass # then traiter les records du job...

    def __cancel(self):
        self.__db.close()

    def __onCancel(self):
        """
        When the Cancel button in Import Jobs Dialog is pushed
        """
        self.__jobsDlg.reject()




