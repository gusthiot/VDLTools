# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2017-11-30
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

from qgis.gui import QgsDualView, QgsAttributeEditorContext
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QMenu


class AttributesTableView(QDialog):
    """
    AttributeTableView class to display filtered attributes table
    """

    def __init__(self, layer, canvas, request):
        """
        Constructor
        """
        QDialog.__init__(self)
        self.setWindowTitle(layer.name())
        self.__layout = QVBoxLayout()
        self.__menu = QMenu()
        for a in layer.actions().listActions():
            self.__menu.addAction(a)
        self.__layout.addWidget(self.__menu)
        self.__dual = QgsDualView()
        self.__context = QgsAttributeEditorContext()
        self.__dual.init(layer, canvas,request, self.__context)
        self.__dual.setView(QgsDualView.AttributeTable)
        self.__layout.addWidget(self.__dual)
        self.setLayout(self.__layout)
