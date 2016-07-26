# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-04-05
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
from math import (pi,
                  atan2,
                  cos,
                  sin)
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor
from qgis.core import (QgsPointV2,
                       QgsLineStringV2,
                       QgsPolygonV2,
                       QGis,
                       QgsGeometry,
                       QgsFeature,
                       QgsMapLayer)
from qgis.gui import (QgsMapTool,
                      QgsRubberBand,
                      QgsMessageBar)
from ..ui.duplicate_attributes_dialog import DuplicateAttributesDialog
from ..ui.duplicate_distance_dialog import DuplicateDistanceDialog
from ..core.finder import Finder
from ..core.geometry_v2 import GeometryV2
from ..core.db_connector import DBConnector


class DuplicateTool(QgsMapTool):

    def __init__(self, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.__canvas = iface.mapCanvas()
        self.__icon_path = ':/plugins/VDLTools/icons/duplicate_icon.png'
        self.__text = 'Duplicate a feature'
        self.setCursor(Qt.ArrowCursor)
        self.__isEditing = 0
        self.__layer = None
        self.__lastFeatureId = None
        self.__selectedFeature = None
        self.__rubberBand = None
        self.__newFeature = None
        self.__oldTool = None

    def icon_path(self):
        return self.__icon_path

    def text(self):
        return self.__text

    def toolName(self):
        return "Duplicate"

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
        types = [QGis.Line, QGis.Polygon]
        if layer is not None\
                and layer.type() == QgsMapLayer.VectorLayer\
                and layer.geometryType() in types:

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

    def __setDistanceDialog(self, isComplexPolygon):
        self.__dstDlg = DuplicateDistanceDialog(isComplexPolygon)
        self.__dstDlg.previewButton().clicked.connect(self.__dstPreview)
        self.__dstDlg.okButton().clicked.connect(self.__dstOk)
        self.__dstDlg.cancelButton().clicked.connect(self.__dstCancel)

    def __setAttributesDialog(self, fields, attributes):
        self.__attDlg = DuplicateAttributesDialog(fields, attributes)
        self.__attDlg.okButton().clicked.connect(self.__attOk)
        self.__attDlg.cancelButton().clicked.connect(self.__attCancel)

    def __dstCancel(self):
        self.__dstDlg.close()
        self.__isEditing = 0
        self.__canvas.scene().removeItem(self.__rubberBand)
        self.__rubberBand = None
        self.__layer.removeSelection()

    def __attCancel(self):
        self.__attDlg.close()
        self.__isEditing = 0
        self.__canvas.scene().removeItem(self.__rubberBand)
        self.__rubberBand = None
        self.__layer.removeSelection()

    @staticmethod
    def angle(point1, point2):
        return atan2(point2.y()-point1.y(), point2.x()-point1.x())

    @staticmethod
    def newPoint(angle, point, distance):
        x = point.x() + cos(angle)*distance
        y = point.y() + sin(angle)*distance
        pt = QgsPointV2(x, y)
        pt.addZValue(point.z())
        return pt

    def __dstPreview(self):
        if self.__rubberBand:
            self.__canvas.scene().removeItem(self.__rubberBand)
            self.__rubberBand = None
        if self.__dstDlg.distanceEditText():
            distance = float(self.__dstDlg.distanceEditText())
            if self.__layer.geometryType() == QGis.Polygon:
                self.__polygonPreview(distance)
            else:
                self.__linePreview(distance)
            color = QColor("red")
            color.setAlphaF(0.78)
            self.__rubberBand.setWidth(2)
            self.__rubberBand.setColor(color)
            self.__rubberBand.setLineStyle(Qt.DotLine)
            self.__rubberBand.show()

    def __linePreview(self, distance):
        line_v2 = GeometryV2.asLineStringV2(self.__selectedFeature.geometry())
        self.__newFeature = QgsLineStringV2()
        self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Line)
        for pos in xrange(line_v2.numPoints()):
            if pos == 0:
                angle = self.angle(line_v2.pointN(pos), line_v2.pointN(pos + 1)) + pi / 2
                dist = distance
            elif pos == (line_v2.numPoints() - 1):
                angle = self.angle(line_v2.pointN(pos - 1), line_v2.pointN(pos)) + pi / 2
                dist = distance
            else:
                angle1 = self.angle(line_v2.pointN(pos - 1), line_v2.pointN(pos))
                angle2 = self.angle(line_v2.pointN(pos), line_v2.pointN(pos + 1))
                angle = float(pi + angle1 + angle2) / 2
                dist = float(distance) / sin(float(pi + angle1 - angle2) / 2)
            self.__newFeature.addVertex(self.newPoint(angle, line_v2.pointN(pos), dist))
        self.__rubberBand.setToGeometry(QgsGeometry(self.__newFeature.clone()), None)

    def __polygonPreview(self, distance):
        self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Polygon)
        polygon_v2 = GeometryV2.asPolygonV2(self.__selectedFeature.geometry())
        self.__newFeature = QgsPolygonV2()
        line_v2 = self.__newLine(polygon_v2.exteriorRing(), distance)
        self.__newFeature.setExteriorRing(line_v2)
        self.__rubberBand.setToGeometry(QgsGeometry(line_v2.clone()), None)
        for num in xrange(polygon_v2.numInteriorRings()):
            if self.__dstDlg.isInverted():
                distance = -distance
            line_v2 = self.__newLine(polygon_v2.interiorRing(num), distance)
            self.__newFeature.addInteriorRing(line_v2)
            self.__rubberBand.addGeometry(QgsGeometry(line_v2.clone()), None)

    def __newLine(self, curve_v2, distance):
        new_line_v2 = QgsLineStringV2()
        line_v2 = curve_v2.curveToLine()
        for pos in xrange(line_v2.numPoints()):
            if pos == 0:
                pos1 = curve_v2.numPoints() - 2
            else:
                pos1 = pos - 1
            pos2 = pos
            if pos == (curve_v2.numPoints() - 1):
                pos3 = 1
            else:
                pos3 = pos + 1
            angle1 = self.angle(line_v2.pointN(pos1), line_v2.pointN(pos2))
            angle2 = self.angle(line_v2.pointN(pos), line_v2.pointN(pos3))
            angle = float(pi + angle1 + angle2) / 2
            dist = float(distance) / sin(float(pi + angle1 - angle2) / 2)
            new_line_v2.addVertex(self.newPoint(angle, line_v2.pointN(pos), dist))
        return new_line_v2

    def __dstOk(self):
        self.__dstPreview()
        self.__dstDlg.close()
    #     self.__setAttributesDialog(self.__layer.pendingFields(), self.__selectedFeature.attributes())
    #     self.__attDlg.show()
    #
    # def __attOk(self):
    #     self.__attDlg.close()
        self.__canvas.scene().removeItem(self.__rubberBand)
        geometry = QgsGeometry(self.__newFeature)
        if not geometry.isGeosValid():
            self.__iface.messageBar().pushMessage("Error", "Geos geometry problem", level=QgsMessageBar.CRITICAL)
        self.__rubberBand = None
        feature = QgsFeature(self.__layer.pendingFields())
        feature.setGeometry(geometry)
        feature.setAttributes(self.__selectedFeature.attributes())
        # feature.setAttributes(self.__attDlg.getAttributes())
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
        self.__layer.addFeature(feature)
        self.__layer.updateExtents()
        self.__isEditing = 0
        self.__layer.removeSelection()

    def canvasMoveEvent(self, event):
        if not self.__isEditing:
            f = Finder.findClosestFeatureAt(event.pos(), self.__layer, self)
            if f is not None and self.__lastFeatureId != f.id():
                self.__lastFeatureId = f.id()
                self.__layer.setSelectedFeatures([f.id()])
            if f is None:
                self.__layer.removeSelection()
                self.__lastFeatureId = None

    def canvasReleaseEvent(self, event):
        found_features = self.__layer.selectedFeatures()
        if len(found_features) > 0:
            if len(found_features) < 1:
                self.__iface.messageBar().pushMessage(u"Une seule feature à la fois", level=QgsMessageBar.INFO)
                return
            self.__selectedFeature = found_features[0]
            self.__isEditing = 1
            if (self.__layer.geometryType() == QGis.Polygon)\
                    and (len(self.__selectedFeature.geometry().asPolygon()) > 1):
                self.__setDistanceDialog(True)
            else:
                self.__setDistanceDialog(False)
            self.__dstDlg.setDistanceEditText("5.0")
            self.__dstDlg.show()
