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
from qgis.core import (QGis,
                       QgsMapLayer)


class MultiAttributesTool(MultiselectTool):
    """
    Map tool class to duplicate an object
    """

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        MultiselectTool.__init__(self, iface)
        self.__iface = iface
        self.__icon_path = ':/plugins/VDLTools/icons/select_icon.png'
        self.__text = QCoreApplication.translate("VDLTools","Select features on multiple layers")
        self.selectedSignal.connect(self.__selected)
        self.__confDlg = None

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

    def toolName(self):
        """
        To get the tool name
        :return: tool name
        """
        return QCoreApplication.translate("VDLTools","Multiselect")

    def setTool(self):
        """
        To set the current tool as this one
        """
        self.canvas().setMapTool(self)

    def __selected(self):
        self.__confDlg = MultiConfirmDialog()
        self.__confDlg.okButton().clicked.connect(self.__onConfirmYes)
        self.__confDlg.cancelButton().clicked.connect(self.__onConfirmNo)
        self.__confDlg.show()

    def __onConfirmNo(self):
        self.__confDlg.reject()

    def __onConfirmYes(self):
        self.__confDlg.accept()
        for layer in self.__iface.mapCanvas().layers():
            if layer.type() == QgsMapLayer.VectorLayer and QGis.fromOldWkbType(layer.wkbType()) in self.types:
                if layer.selectedFeatureCount() > 0:
                    ids = "("
                    c = False
                    for f in layer.selectedFeatures():
                        if c:
                            ids += ","
                        else:
                            c = True
                        ids += str(f.id())
                    ids += ")"
                    print(layer.name(), layer.selectedFeatureCount(), ids)
                    self.__iface.showAttributeTable(layer, "$id IN {}".format(ids))
