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

from qgis.gui import (QgsAttributeTableModel,
                      QgsAttributeTableFilterModel,
                      QgsAttributeTableView)
from qgis.core import QgsVectorLayerCache


class AttributesTableView(QgsAttributeTableView):
    """
    AttributeTableView class to display filtered attributes table
    """

    def __init__(self, layer, canvas):
        """
        Constructor
        """
        QgsAttributeTableView.__init__(self)
        self.__layer = layer
        self.__canvas = canvas
        self.setWindowTitle(self.__layer.name())
        self.__layerCache = QgsVectorLayerCache(self.__layer, 10000)
        self.__tableModel = QgsAttributeTableModel(self.__layerCache)
        self.__tableModel.loadLayer()
        self.__tableFilterModel = QgsAttributeTableFilterModel(self.__canvas, self.__tableModel)
        self.__tableFilterModel.setFilterMode(QgsAttributeTableFilterModel.ShowSelected)
        self.setModel(self.__tableFilterModel)
