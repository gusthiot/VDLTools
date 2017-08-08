# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2017-01-31
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
from PyQt4.QtCore import pyqtSignal
from qgis.core import (QGis,
                       QgsFeatureRequest,
                       QgsRenderContext,
                       QgsProject,
                       QgsRectangle,
                       QgsMapLayer)
from area_tool import AreaTool


class MultiselectTool(AreaTool):
    """
    Map tool class to select object from multiple layers
    """

    selectedSignal = pyqtSignal()

    def __init__(self, iface, identified=False):
        """
        Constructor
        :param iface: interface
        """
        AreaTool.__init__(self, iface)
        # self.types = [QgsWKBTypes.PointZ, QgsWKBTypes.LineStringZ, QgsWKBTypes.CircularStringZ,
        #               QgsWKBTypes.CompoundCurveZ, QgsWKBTypes.CurvePolygonZ, QgsWKBTypes.PolygonZ]
        self.types = [QGis.Point, QGis.Line, QGis.Polygon]
        self.releasedSignal.connect(self.__select)
        self.identified = identified

    def disabled(self):
        return QgsProject.instance().readListEntry("Identify", "disabledLayers", "None")[0]

    def __select(self):
        """
        To select objects in multiples layers inside a selection rectangle
        """
        searchRect = QgsRectangle(self.first, self.last)
        for layer in self.canvas().layers():
            if not self.identified or layer.id() not in self.disabled():
                if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() in self.types:
                    renderer = layer.rendererV2()
                    context = QgsRenderContext()
                    if renderer:
                        renderer.startRender(context,layer.pendingFields())
                        request = QgsFeatureRequest()
                        request.setFilterRect(searchRect)
                        request.setFlags(QgsFeatureRequest.ExactIntersect)
                        fIds = []
                        for feature in layer.getFeatures(request):
                            will = renderer.willRenderFeature(feature, context)
                            if will:
                                fIds.append(feature.id())
                        renderer.stopRender(context)
                        layer.selectByIds(fIds)

        self.selectedSignal.emit()
