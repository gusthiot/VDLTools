# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2019-11-21
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

import traceback
from PyQt4.QtCore import QThread, pyqtSignal


class BackWorker(QThread):

    # progressSignal = pyqtSignal(float)
    finishedSignal = pyqtSignal(object)
    errorSignal = pyqtSignal(Exception, basestring)

    def __init__(self, iface):
        QThread.__init__(self)
        self.__iface = iface
        # self.killed = False

    def run(self):
        ret = None
        snap_util = self.__iface.mapCanvas().snappingUtils()
        extent = self.__iface.mapCanvas().extent()
        try:
            lcs_list = snap_util.layers()
            step = 0
            for lc in lcs_list:
                # if self.killed:
                #     break
                locator = snap_util.locatorForLayer(lc.layer)
                locator.setExtent(extent)
                if not locator.hasIndex():
                    locator.init()
                else:
                    locator.rebuildIndex()
                # self.progressSignal.emit(100 * step / len(lcs_list))
                step += 1
        except Exception as e:
            print(e)
            self.errorSignal.emit(e, traceback.format_exc())
        self.finishedSignal.emit(ret)

    # def kill(self):
    #     self.killed = True
