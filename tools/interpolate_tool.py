# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-05-30
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

from qgis.gui import (QgsMapTool, QgsMessageBar)
from qgis.core import (QGis,
                       QgsMapLayer, QgsFeature, QgsGeometry, QgsPointV2, QgsVertexId,
                       QgsWKBTypes)
from PyQt4.QtCore import Qt
from ..core.finder import Finder
from math import sqrt, pow
from ..ui.interpolate_confirm_dialog import InterpolateConfirmDialog


class InterpolateTool(QgsMapTool):

    def __init__(self, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.__canvas = iface.mapCanvas()
        self.__icon_path = ':/plugins/VDLTools/icons/interpolate_icon.png'
        self.__text = 'Interpolate the elevation of a vertex and a point in the middle of a line'
        self.__oldTool = None
        self.__layer = None
        self.setCursor(Qt.ArrowCursor)
        self.__isEditing = 0
        self.__lastFeatureId = None
        self.__layerList = None
        self.__lastLayer = None
        self.__confDlg = None
        self.__mapPoint = None

    def icon_path(self):
        return self.__icon_path

    def text(self):
        return self.__text

    def setTool(self):
        self.__oldTool = self.__canvas.mapTool()
        self.__canvas.setMapTool(self)

    def activate(self):
        QgsMapTool.activate(self)
        self.__updateList()

    def deactivate(self):
        QgsMapTool.deactivate(self)

    def startEditing(self):
        self.action().setEnabled(True)
        self.__canvas.layersChanged.connect(self.__updateList)
        self.__layer.editingStarted.disconnect(self.startEditing)
        self.__layer.editingStopped.connect(self.stopEditing)

    def stopEditing(self):
        self.action().setEnabled(False)
        self.__canvas.layersChanged.disconnect(self.__updateList)
        self.__layer.editingStopped.disconnect(self.stopEditing)
        self.__layer.editingStarted.connect(self.startEditing)
        if self.__canvas.mapTool == self:
            self.__canvas.setMapTool(self.__oldTool)

    def removeLayer(self):
        if self.__layer is not None:
            if self.__layer.isEditable():
                self.__layer.editingStopped.disconnect(self.stopEditing)
            else:
                self.__layer.editingStarted.disconnect(self.startEditing)
            self.__layer = None

    def setEnable(self, layer):
        if layer is not None \
                and layer.type() == QgsMapLayer.VectorLayer \
                and QGis.fromOldWkbType(layer.wkbType()) == QgsWKBTypes.PointZ:

            if layer == self.__layer:
                return

            if self.__layer is not None:
                if self.__layer.isEditable():
                    self.__layer.editingStopped.disconnect(self.stopEditing)
                else:
                    self.__layer.editingStarted.disconnect(self.startEditing)
            self.__layer = layer
            if self.__layer.isEditable():
                self.action().setEnabled(True)
                self.__layer.editingStopped.connect(self.stopEditing)
                self.__canvas.layersChanged.connect(self.__updateList)
            else:
                self.action().setEnabled(False)
                self.__layer.editingStarted.connect(self.startEditing)
                if self.__canvas.mapTool == self:
                    self.__canvas.setMapTool(self.__oldTool)
            return
        self.action().setEnabled(False)
        self.removeLayer()

    def __updateList(self):
        self.__layerList = []
        for layer in self.__iface.mapCanvas().layers():
            if layer is not None \
                    and layer.type() == QgsMapLayer.VectorLayer \
                    and QGis.fromOldWkbType(layer.wkbType()) == QgsWKBTypes.LineStringZ:
                self.__layerList.append(layer)

    def canvasMoveEvent(self, event):
        if not self.__isEditing and self.__layerList is not None:
            f_l = Finder.findClosestFeatureLayersAt(event.pos(), self.__layerList, self)

            if f_l is not None and self.__lastFeatureId != f_l[0].id():
                f = f_l[0]
                l = f_l[1]
                self.__lastFeatureId = f.id()
                self.__lastLayer = l
                self.__lastLayer.setSelectedFeatures([f.id()])
            if f_l is None and self.__lastLayer is not None:
                self.__lastLayer.removeSelection()
                self.__lastFeatureId = None

    def canvasReleaseEvent(self, event):
        if self.__lastLayer is not None:
            found_features = self.__lastLayer.selectedFeatures()
            if len(found_features) > 0:
                if len(found_features) < 1:
                    self.__iface.messageBar().pushMessage(u"Une seule feature à la fois",
                                                          level=QgsMessageBar.INFO)
                    return
                self.__selectedFeature = found_features[0]
                self.__mapPoint = event.mapPoint()
                if self.__lastLayer.isEditable() is False:
                    self.__confDlg = InterpolateConfirmDialog()
                    self.__confDlg.allButton().clicked.connect(self.__onConfirmedAll)
                    self.__confDlg.ptButton().clicked.connect(self.__onConfirmedPoint)
                    self.__confDlg.cancelButton().clicked.connect(self.__onCloseConfirm)
                    self.__confDlg.show()
                else:
                    self.__createElements(True)

    def __closeConfirmDialog(self):
        self.__confDlg.close()
        self.__confDlg.allButton().clicked.disconnect(self.__onConfirmedAll)
        self.__confDlg.ptButton().clicked.disconnect(self.__onConfirmedPoint)
        self.__confDlg.cancelButton().clicked.disconnect(self.__onCloseConfirm)

    def __onCloseConfirm(self):
        self.__closeConfirmDialog()

    def __onConfirmedPoint(self):
        self.__closeConfirmDialog()
        self.__createElements(False)

    def __onConfirmedAll(self):
        self.__closeConfirmDialog()
        self.__lastLayer.startEditing()
        self.__createElements(True)

    def __createElements(self, withVertex):
        self.__isEditing = 1
        print("take geom")
        line = self.__selectedFeature.geometry()
        print("after take")
        line_v2 = line.geometry()
        vertex_v2 = QgsPointV2()
        vertex_id = QgsVertexId()
        line_v2.closestSegment(QgsPointV2(self.__mapPoint), vertex_v2, vertex_id, 0)

        x0 = line_v2.xAt(vertex_id.vertex-1)
        y0 = line_v2.yAt(vertex_id.vertex-1)
        d0 = self.distance(x0, vertex_v2.x(), y0, vertex_v2.y())
        x1 = line_v2.xAt(vertex_id.vertex)
        y1 = line_v2.yAt(vertex_id.vertex)
        d1 = self.distance(x1, vertex_v2.x(), y1, vertex_v2.y())
        z0 = line_v2.zAt(vertex_id.vertex-1)
        z1 = line_v2.zAt(vertex_id.vertex)

        print("add point")
        vertex_v2.addZValue((d0*z1 + d1*z0)/(d0 + d1))
        pt_feat = QgsFeature(self.__layer.pendingFields())
        pt_feat.setGeometry(QgsGeometry(vertex_v2))
        self.__layer.addFeature(pt_feat)
        if withVertex:
            print("insert")
            line_v2.insertVertex(vertex_id, vertex_v2)
            print("change geom")
            if self.__lastLayer.changeGeometry(self.__selectedFeature.id(), QgsGeometry(line_v2)) is False:
                print("False")
            self.__lastLayer.updateExtents()
        self.__layer.updateExtents()
        print("refresh")
        self.__canvas.refresh()
        self.__lastLayer.removeSelection()
        self.__lastFeatureId = None
        self.__isEditing = 0

    @staticmethod
    def distance(x1, x2, y1, y2):
        return sqrt(pow(x1-x2, 2) + pow(y1-y2, 2))
