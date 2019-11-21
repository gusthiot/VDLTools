# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2019-11-05
        git sha              : $Format:%H$
        copyright            : (C) 2019 Ville de Lausanne
        author               : Ingénierie Informatique Gusthiot, Christophe Gusthiot
        email                : i2g@gusthiot.ch
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
from future.builtins import object
from .back_worker import BackWorker

from PyQt4.QtCore import QCoreApplication, Qt
from PyQt4.QtGui import QProgressBar, QPushButton
from qgis.gui import QgsMessageBar


class RebuildIndex(object):
    """
    Class to
    """

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        self.__iface = iface
        self.icon_path = ':/plugins/VDLTools/icons/rebuild_icon.png'
        self.text = QCoreApplication.translate("VDLTools", "Rebuild Index")

    def start(self):
        """
        To start the rebuild
        """
        self.__backWorker = BackWorker(self.__iface)
        progressBar = QProgressBar()
        progressBar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        cancelButton = QPushButton()
        cancelButton.setText('Cancel')
        cancelButton.clicked.connect(self.__backWorker.kill)
        self.__messageBar = self.__iface.messageBar().createMessage('Rebuild Index...', )
        self.__messageBar.layout().addWidget(progressBar)
        self.__messageBar.layout().addWidget(cancelButton)
        self.__iface.messageBar().pushWidget(self.__messageBar, self.__iface.messageBar().INFO)

        self.__backWorker.finishedSignal.connect(self.finished)
        self.__backWorker.errorSignal.connect(self.error)
        self.__backWorker.progressSignal.connect(progressBar.setValue)
        self.__backWorker.start()

    def finished(self):
        self.__backWorker.quit()
        self.__backWorker.wait()
        self.__backWorker.deleteLater()
        self.__iface.messageBar().popWidget(self.__messageBar)

    def error(self, e, exception_string):
        self.__iface.messageBar().pushMessage(
            QCoreApplication.translate("VDLTools", "Worker thread raised an exception:\n") + format(exception_string),
            level=QgsMessageBar.CRITICAL, duration=0)


