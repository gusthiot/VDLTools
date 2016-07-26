# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-07-12
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
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor
from qgis.core import (QgsPointV2,
                       QgsLineStringV2,
                       QgsVertexId,
                       QgsSnapper,
                       QgsTolerance,
                       QgsFeature,
                       QgsPolygonV2,
                       QGis,
                       QgsGeometry,
                       QgsMapLayer)
from qgis.gui import (QgsMapTool,
                      QgsRubberBand,
                      QgsMessageBar)
from ..ui.move_confirm_dialog import MoveConfirmDialog
from ..core.finder import Finder
from ..core.db_connector import DBConnector
from ..core.geometry_v2 import GeometryV2


class MoveTool(QgsMapTool):

    def __init__(self, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.__canvas = iface.mapCanvas()
        self.__icon_path = ':/plugins/VDLTools/icons/move_icon.png'
        self.__text = 'Move/Copy a feature'
        self.setCursor(Qt.ArrowCursor)
        self.__isEditing = 0
        self.__findVertex = 0
        self.__onMove = 0
        self.__counter = 0
        self.__layer = None
        self.__oldTool = None
        self.__confDlg = None
        self.__lastFeatureId = None
        self.__selectedFeature = None
        self.__rubberBand = None
        self.__rubberSnap = None
        self.__newFeature = None
        self.__selectedVertex = None

    def icon_path(self):
        return self.__icon_path

    def text(self):
        return self.__text

    def toolName(self):
        return "Move/Copy"

    def activate(self):
        QgsMapTool.activate(self)

    def deactivate(self):
        QgsMapTool.deactivate(self)

    def startEditing(self):
        self.action().setEnabled(True)
        self.__layer.editingStarted.disconnect(self.startEditing)
        self.__layer.editingStopped.connect(self.stopEditing)

    def stopEditing(self):
        self.action().setEnabled(False)
        self.__layer.editingStopped.disconnect(self.stopEditing)
        self.__layer.editingStarted.connect(self.startEditing)
        if self.__canvas.mapTool == self:
            self.__canvas.setMapTool(self.__oldTool)

    def setTool(self):
        self.__oldTool = self.__canvas.mapTool()
        self.__canvas.setMapTool(self)

    def removeLayer(self):
        if self.__layer is not None:
            if self.__layer.isEditable():
                self.__layer.editingStopped.disconnect(self.stopEditing)
            else:
                self.__layer.editingStarted.disconnect(self.startEditing)
            self.__layer = None

    def setEnable(self, layer):
        if layer is not None\
                and layer.type() == QgsMapLayer.VectorLayer:
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
            else:
                self.action().setEnabled(False)
                self.__layer.editingStarted.connect(self.startEditing)
                if self.__canvas.mapTool == self:
                    self.__canvas.setMapTool(self.__oldTool)
            return
        self.action().setEnabled(False)
        self.removeLayer()

    def __pointPreview(self, point):
        point_v2 = GeometryV2.asPointV2(self.__selectedFeature.geometry())
        self.__newFeature = QgsPointV2(point.x(), point.y())
        self.__newFeature.addZValue(point_v2.z())
        self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Point)
        self.__rubberBand.setToGeometry(QgsGeometry(self.__newFeature.clone()), None)

    def __linePreview(self, point):
        line_v2 = GeometryV2.asLineStringV2(self.__selectedFeature.geometry())
        vertex = line_v2.pointN(self.__selectedVertex)
        dx = vertex.x() - point.x()
        dy = vertex.y() - point.y()
        self.__newFeature = QgsLineStringV2()
        self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Line)
        for pos in xrange(line_v2.numPoints()):
            x = line_v2.pointN(pos).x() - dx
            y = line_v2.pointN(pos).y() - dy
            pt = QgsPointV2(x, y)
            pt.addZValue(line_v2.pointN(pos).z())
            self.__newFeature.addVertex(pt)
        self.__rubberBand.setToGeometry(QgsGeometry(self.__newFeature.clone()), None)

    def __polygonPreview(self, point):
        polygon_v2 = GeometryV2.asPolygonV2(self.__selectedFeature.geometry())
        vertex = polygon_v2.vertexAt(self.__polygonVertexId(polygon_v2))
        dx = vertex.x() - point.x()
        dy = vertex.y() - point.y()
        self.__newFeature = QgsPolygonV2()
        self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Polygon)
        line_v2 = self.__newLine(polygon_v2.exteriorRing(), dx, dy)
        self.__newFeature.setExteriorRing(line_v2)
        self.__rubberBand.setToGeometry(QgsGeometry(line_v2.clone()), None)
        for num in xrange(polygon_v2.numInteriorRings()):
            line_v2 = self.__newLine(polygon_v2.interiorRing(num), dx, dy)
            self.__newFeature.addInteriorRing(line_v2)
            self.__rubberBand.addGeometry(QgsGeometry(line_v2.clone()), None)

    def __polygonVertexId(self, polygon_v2):
        eR = polygon_v2.exteriorRing()
        if self.__selectedVertex < eR.numPoints():
            return QgsVertexId(0, 0, self.__selectedVertex, 1)
        else:
            sel = self.__selectedVertex - eR.numPoints()
            for num in xrange(polygon_v2.numInteriorRings()):
                iR = polygon_v2.interiorRing(num)
                if sel < iR.numPoints():
                    return QgsVertexId(0, num+1, sel, 1)
                sel -= iR.numPoints()

    def __newLine(self, curve_v2, dx, dy):
        new_line_v2 = QgsLineStringV2()
        line_v2 = curve_v2.curveToLine()
        for pos in xrange(line_v2.numPoints()):
            x = line_v2.pointN(pos).x() - dx
            y = line_v2.pointN(pos).y() - dy
            pt = QgsPointV2(x, y)
            pt.addZValue(line_v2.pointN(pos).z())
            new_line_v2.addVertex(pt)
        return new_line_v2

    def __updateSnapperList(self):
        self.__snapperList = []
        self.__layerList = []
        legend = self.__iface.legendInterface()
        scale = self.__iface.mapCanvas().mapRenderer().scale()
        for layer in self.__iface.mapCanvas().layers():
            if layer.type() == QgsMapLayer.VectorLayer and layer.hasGeometryType():
                if not layer.hasScaleBasedVisibility() or layer.minimumScale() < scale <= layer.maximumScale():
                    if legend.isLayerVisible(layer):
                        snapLayer = QgsSnapper.SnapLayer()
                        snapLayer.mLayer = layer
                        snapLayer.mSnapTo = QgsSnapper.SnapToVertex
                        snapLayer.mTolerance = 7
                        snapLayer.mUnitType = QgsTolerance.Pixels
                        self.__snapperList.append(snapLayer)
                        self.__layerList.append(layer)

    def __onCloseConfirm(self):
        self.__confDlg.close()
        self.__confDlg.moveButton().clicked.disconnect(self.__onConfirmedMove)
        self.__confDlg.copyButton().clicked.disconnect(self.__onConfirmedCopy)
        self.__confDlg.cancelButton().clicked.disconnect(self.__onCloseConfirm)
        self.__rubberBand.reset()
        self.__rubberSnap.reset()
        self.__isEditing = 0
        self.__lastFeatureId = None
        self.__selectedFeature = None
        self.__rubberBand = None
        self.__rubberSnap = None
        self.__newFeature = None
        self.__selectedVertex = None
        self.__layer.removeSelection()

    def __onConfirmedMove(self):
        geometry = QgsGeometry(self.__newFeature)
        if not geometry.isGeosValid():
            self.__iface.messageBar().pushMessage("Error", "Geos geometry problem", level=QgsMessageBar.CRITICAL)
        self.__layer.changeGeometry(self.__selectedFeature.id(), geometry)
        self.__layer.updateExtents()
        self.__onCloseConfirm()

    def __onConfirmedCopy(self):
        geometry = QgsGeometry(self.__newFeature)
        if not geometry.isGeosValid():
            self.__iface.messageBar().pushMessage("Error", "Geos geometry problem", level=QgsMessageBar.CRITICAL)
        feature = QgsFeature(self.__layer.pendingFields())
        feature.setGeometry(geometry)
        feature.setAttributes(self.__selectedFeature.attributes())
        if self.__layer.providerType() == "postgres":
            conn = DBConnector.getConnections()
            db = DBConnector.setConnection(conn[0], self.__iface)
            if db:
                primary, next_val = DBConnector.getPrimary(self.__layer, db)
                if primary:
                    feature.setAttribute(primary, next_val)
                else:
                    self.__iface.messageBar().pushMessage("Error",
                                                          "no primary key field found, you have to fix it manually",
                                                          level=QgsMessageBar.CRITICAL)
                db.close()
        self.__iface.openFeatureForm(self.__layer, feature)
        # self.__layer.addFeature(feature)
        self.__layer.updateExtents()
        self.__onCloseConfirm()

    def canvasMoveEvent(self, event):
        if not self.__isEditing and not self.__findVertex and not self.__onMove:
            f = Finder.findClosestFeatureAt(event.pos(), self.__layer, self)
            if f is not None and self.__lastFeatureId != f.id():
                self.__lastFeatureId = f.id()
                self.__layer.setSelectedFeatures([f.id()])
            if f is None:
                self.__layer.removeSelection()
                self.__lastFeatureId = None
        elif self.__findVertex:
            self.__rubberBand.reset()
            closest = self.__selectedFeature.geometry().closestVertex(event.mapPoint())
            color = QColor("red")
            color.setAlphaF(0.78)
            self.__rubberBand.setColor(color)
            self.__rubberBand.setIcon(4)
            self.__rubberBand.setIconSize(20)
            self.__rubberBand.setToGeometry(QgsGeometry().fromPoint(closest[0]), None)
        elif self.__onMove:
            if self.__rubberBand:
                self.__rubberBand.reset()
            if self.__layer.geometryType() == QGis.Polygon:
                self.__polygonPreview(event.mapPoint())
            elif self.__layer.geometryType() == QGis.Line:
                self.__linePreview(event.mapPoint())
            else:
                self.__pointPreview(event.mapPoint())
            color = QColor("red")
            color.setAlphaF(0.78)
            self.__rubberBand.setColor(color)
            if self.__layer.geometryType() != QGis.Point:
                self.__rubberBand.setWidth(2)
                self.__rubberBand.setLineStyle(Qt.DotLine)
            else:
                self.__rubberBand.setIcon(4)
                self.__rubberBand.setIconSize(20)
            if self.__counter > 2:
                if self.__rubberSnap:
                    self.__rubberSnap.reset()
                else:
                    self.__rubberSnap = QgsRubberBand(self.__canvas, QGis.Point)
                self.__rubberSnap.setColor(color)
                self.__rubberSnap.setIconSize(20)
                snappedIntersection = Finder.snapToIntersection(event.pos(), self, self.__layerList)
                if snappedIntersection is None:
                    snappedPoint = Finder.snapToLayers(event.pos(), self.__snapperList, self.__canvas)
                    if snappedPoint is not None:
                        self.__rubberSnap.setIcon(4)
                        self.__rubberSnap.setToGeometry(QgsGeometry().fromPoint(snappedPoint), None)
                else:
                    self.__rubberSnap.setIcon(1)
                    self.__rubberSnap.setToGeometry(QgsGeometry().fromPoint(snappedIntersection), None)
                self.__counter = 0
            else:
                self.__counter += 1

    def canvasReleaseEvent(self, event):
        if not self.__isEditing and not self.__findVertex and not self.__onMove:
            found_features = self.__layer.selectedFeatures()
            if len(found_features) > 0:
                if len(found_features) < 1:
                    self.__iface.messageBar().pushMessage(u"Une seule feature à la fois", level=QgsMessageBar.INFO)
                    return
                self.__selectedFeature = found_features[0]
                if self.__layer.geometryType() != QGis.Point:
                    self.__findVertex = 1
                    self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Point)
                else:
                    self.__onMove = 1
                    self.__updateSnapperList()
        elif self.__findVertex:
            self.__findVertex = 0
            closest = self.__selectedFeature.geometry().closestVertex(event.mapPoint())
            self.__selectedVertex = closest[1]
            self.__onMove = 1
            self.__updateSnapperList()
        elif self.__onMove:
            self.__onMove = 0
            mapPoint = event.mapPoint()
            snappedIntersection = Finder.snapToIntersection(event.pos(), self, self.__layerList)
            if snappedIntersection is None:
                snappedPoint = Finder.snapToLayers(event.pos(), self.__snapperList, self.__canvas)
                if snappedPoint is not None:
                    mapPoint = snappedPoint
            else:
                mapPoint = snappedIntersection
            self.__isEditing = 1
            if self.__rubberBand:
                self.__rubberBand.reset()
            if self.__layer.geometryType() == QGis.Polygon:
                self.__polygonPreview(mapPoint)
            elif self.__layer.geometryType() == QGis.Line:
                self.__linePreview(mapPoint)
            else:
                self.__pointPreview(mapPoint)
            color = QColor("red")
            color.setAlphaF(0.78)
            self.__rubberBand.setColor(color)
            if self.__layer.geometryType() != QGis.Point:
                self.__rubberBand.setWidth(2)
                self.__rubberBand.setLineStyle(Qt.DotLine)
            else:
                self.__rubberBand.setIcon(4)
                self.__rubberBand.setIconSize(20)
            self.__confDlg = MoveConfirmDialog()
            self.__confDlg.moveButton().clicked.connect(self.__onConfirmedMove)
            self.__confDlg.copyButton().clicked.connect(self.__onConfirmedCopy)
            self.__confDlg.cancelButton().clicked.connect(self.__onCloseConfirm)
            self.__confDlg.show()
