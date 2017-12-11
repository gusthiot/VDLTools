# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2017-02-06
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
from __future__ import division
from PyQt4.QtCore import QCoreApplication
from .multiselect_tool import MultiselectTool
from ..ui.multi_confirm_dialog import MultiConfirmDialog
# from ..ui.attributes_table_view import AttributesTableView
from qgis.core import QgsMapLayer
# import time


class MultiAttributesTool(MultiselectTool):
    """
    Map tool class to display attributes tables from different objects from multiple layers
    """

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        MultiselectTool.__init__(self, iface, True)
        self.__iface = iface
        self.icon_path = ':/plugins/VDLTools/icons/select_icon.png'
        self.text = QCoreApplication.translate("VDLTools", "Select features on multiple layers")
        self.selectedSignal.connect(self.__selected)
        self.__confDlg = None
        # self.__tables = []

    def toolName(self):
        """
        To get the tool name
        :return: tool name
        """
        return QCoreApplication.translate("VDLTools", "Multiselect")

    def setTool(self):
        """
        To set the current tool as this one
        """
        self.canvas().setMapTool(self)

    def __selected(self):
        """
        When search polygon is selected
        """
        self.__confDlg = MultiConfirmDialog()
        self.__confDlg.okButton().clicked.connect(self.__onConfirmYes)
        self.__confDlg.cancelButton().clicked.connect(self.__onConfirmNo)
        self.__confDlg.show()

    def __onConfirmNo(self):
        """
        When the No button in Multi Confirm Dialog is pushed
        """
        self.__confDlg.reject()

    def __onConfirmYes(self):
        """
        When the Yes button in Multi Confirm Dialog is pushed
        """
        self.__confDlg.accept()
        # i = 0
        for layer in self.canvas().layers():
            # start = time.time()
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() in self.types:
                if layer.selectedFeatureCount() > 0 and layer.id() not in self.disabled():
                    ids = "("
                    c = False
                    for f in layer.selectedFeatures():
                        if c:
                            ids += ","
                        else:
                            c = True
                        ids += str(f.id())
                    ids += ")"
                   #  tableDlg = AttributesTableView(layer, self.canvas(), self.request)
                   #  self.__tables.append(tableDlg)
                   #  self.__tables[i].show()
                   #  i += 1
                    self.__iface.showAttributeTable(layer, "$id IN {}".format(ids))
            # print(" %s seconds to show %s" % (time.time() - start, layer.name()))
