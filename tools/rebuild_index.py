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

from PyQt4.QtCore import QCoreApplication
# from PyQt4.QtGui import QProgressBar, QPushButton, QProgressDialog
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
        self.killed = False

    def start(self):
        """
        To start the rebuild
        """

        self.__backWorker = BackWorker(self.__iface)

        self.__backWorker.finishedSignal.connect(self.finished)
        self.__backWorker.errorSignal.connect(self.error)
        # self.__backWorker.progressSignal.connect(progressBar.setValue)
        self.__backWorker.start()

        # snap_util = self.__iface.mapCanvas().snappingUtils()
        # extent = self.__iface.mapCanvas().extent()
        # self.__progressDialog = QProgressDialog()
        # self.__progressDialog.setWindowTitle("Rebuild Index...")
        # self.__progressDialog.setLabelText("text")
        # progressBar = QProgressBar(self.__progressDialog)
        # progressBar.setTextVisible(True)
        # cancelButton = QPushButton()
        # cancelButton.setText('Cancel')
        # cancelButton.clicked.connect(self.kill)
        # self.__progressDialog.setBar(progressBar)
        # self.__progressDialog.setCancelButton(cancelButton)
        # self.__progressDialog.setMinimumWidth(300)
        # self.__progressDialog.show()

        # lcs_list = snap_util.layers()
        # step = 0
        # self.killed = False
        # for lc in lcs_list:
        #     if self.killed:
        #         break
        #     locator = snap_util.locatorForLayer(lc.layer)
        #     locator.setExtent(extent)
        #     if not locator.hasIndex():
        #         locator.init()
        #     else:
        #         locator.rebuildIndex()
        #     progressBar.setValue(100 * step / len(lcs_list))
        #     step += 1
        # self.__progressDialog.close()

    # def kill(self):
    #     self.killed = True

    def finished(self):
        self.__backWorker.quit()
        self.__backWorker.wait()
        self.__backWorker.deleteLater()
        # self.__progressDialog.close()

    def error(self, e, exception_string):
        self.__iface.messageBar().pushMessage(
            QCoreApplication.translate("VDLTools", "Worker thread raised an exception:\n") + format(exception_string),
            level=QgsMessageBar.CRITICAL, duration=0)
