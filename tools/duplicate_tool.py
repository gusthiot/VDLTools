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
from qgis.core import (QgsPoint,
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
        self.__newFeatures = None
        self.__oldTool = None
        self.__vectorKind = QgsMapLayer.VectorLayer
        self.__wkbLine = QGis.WKBLineString
        self.__wkbPolygon = QGis.WKBPolygon

    def icon_path(self):
        return self.__icon_path

    def text(self):
        return self.__text

    def setEnable(self, layer):
        self.__setLayer(layer)

    def activate(self):
        QgsMapTool.activate(self)

    def deactivate(self):
        if self.__layer is not None:
            self.__layer.editingStarted.disconnect()
            self.__layer.editingStopped.disconnect()
        QgsMapTool.deactivate(self)

    def startEditing(self):
        self.action().setEnabled(True)

    def stopEditing(self):
        self.action().setEnabled(False)
        if self.__canvas.mapTool != self:
            self.__canvas.setMapTool(self.__oldTool)

    def setTool(self):
        self.__oldTool = self.__canvas.mapTool()
        self.__canvas.setMapTool(self)

    def __setLayer(self, layer):
        if layer is not None\
                and layer.type() == self.__vectorKind\
                and (layer.wkbType() == self.__wkbLine or layer.wkbType() == self.__wkbPolygon):

            if self.__layer is not None:
                self.__layer.editingStarted.disconnect()
                self.__layer.editingStopped.disconnect()
            self.__layer = layer
            if self.__layer.isEditable():
                self.action().setEnabled(True)
            else:
                self.action().setEnabled(False)
                if self.__canvas.mapTool != self:
                    self.__canvas.setMapTool(self.__oldTool)
            self.__layer.editingStarted.connect(self.startEditing)
            self.__layer.editingStopped.connect(self.stopEditing)
            return
        self.action().setEnabled(False)
        self.__layer = None

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
        return QgsPoint(x,y)

    def __dstPreview(self):
        if self.__rubberBand:
            self.__canvas.scene().removeItem(self.__rubberBand)
            self.__rubberBand = None
        if self.__dstDlg.distanceEditText():
            distance = float(self.__dstDlg.distanceEditText())
            if self.__layer.wkbType() == QGis.WKBPolygon:
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
        points = self.__selectedFeature.geometry().asPolyline()
        self.__newFeatures = []
        self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Line)
        for pos in range(0, len(points)):
            if pos == 0:
                angle = self.angle(points[pos], points[pos + 1]) + pi / 2
                dist = distance
            elif pos == (len(points) - 1):
                angle = self.angle(points[pos - 1], points[pos]) + pi / 2
                dist = distance
            else:
                angle1 = self.angle(points[pos - 1], points[pos])
                angle2 = self.angle(points[pos], points[pos + 1])
                angle = float(pi + angle1 + angle2) / 2
                dist = float(distance) / sin(float(pi + angle1 - angle2) / 2)
            self.__newFeatures.append(self.newPoint(angle, points[pos], dist))
        self.__rubberBand.setToGeometry(QgsGeometry.fromPolyline(self.__newFeatures), None)

    def __polygonPreview(self, distance):
        self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Polygon)
        lines = self.__selectedFeature.geometry().asPolygon()
        self.__newFeatures = []
        nb = 0
        for points in lines:
            newPoints = []
            if nb == 1:
                if self.__dstDlg.isInverted():
                    distance = -distance
            for pos in range(0, len(points)):
                if pos == 0:
                    pos1 = len(points) - 2
                else:
                    pos1 = pos - 1
                pos2 = pos
                if pos == (len(points) - 1):
                    pos3 = 1
                else:
                    pos3 = pos + 1
                angle1 = self.angle(points[pos1], points[pos2])
                angle2 = self.angle(points[pos], points[pos3])
                angle = float(pi + angle1 + angle2) / 2
                dist = float(distance) / sin(float(pi + angle1 - angle2) / 2)
                newPoints.append(self.newPoint(angle, points[pos], dist))
            self.__newFeatures.append(newPoints)
            if nb == 0:
                self.__rubberBand.setToGeometry(QgsGeometry.fromPolyline(newPoints), None)
            else:
                self.__rubberBand.addGeometry(QgsGeometry.fromPolyline(newPoints), None)
            nb += 1

    def __dstOk(self):
        self.__dstPreview()
        self.__dstDlg.close()
        self.__setAttributesDialog(self.__layer.pendingFields(), self.__selectedFeature.attributes())
        self.__attDlg.show()

    def __attOk(self):
        self.__attDlg.close()
        self.__canvas.scene().removeItem(self.__rubberBand)
        self.__rubberBand = None
        if self.__layer.wkbType() == QGis.WKBPolygon:
            geometry = QgsGeometry.fromPolygon(self.__newFeatures)
        else:
            geometry = QgsGeometry.fromPolyline(self.__newFeatures)
        if not geometry.isGeosValid():
            print "geometry problem"

        feature = QgsFeature(self.__layer.pendingFields())
        feature.setGeometry(geometry)
        feature.setAttributes(self.__attDlg.getAttributes())
        self.__layer.addFeature(feature)
        self.__layer.updateExtents()
        self.__isEditing = 0
        self.__layer.removeSelection()

    def canvasMoveEvent(self, event):
        if not self.__isEditing:
            f = Finder.findClosestFeatureAt(event.pos(), self.__layer, self)
            if f and self.__lastFeatureId != f.id():
                self.__lastFeatureId = f.id()
                self.__layer.setSelectedFeatures([f.id()])
            if not f:
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
            if (self.__layer.wkbType() == QGis.WKBPolygon)\
                    and (len(self.__selectedFeature.geometry().asPolygon()) > 1):
                self.__setDistanceDialog(True)
            else:
                self.__setDistanceDialog(False)
            self.__dstDlg.setDistanceEditText("5.0")
            self.__dstDlg.show()
