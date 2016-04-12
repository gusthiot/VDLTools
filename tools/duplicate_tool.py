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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from math import *

from duplicate_distance_dialog import DuplicateDistanceDialog
from duplicate_attributes_dialog import DuplicateAttributesDialog


class DuplicateTool(QgsMapTool):

    def __init__(self, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.dstDlg = None
        self.icon_path = ':/plugins/VDLTools/tools/duplicate_icon.png'
        self.text = 'Duplicate a feature'
        self.setCursor(Qt.ArrowCursor)
        self.isEditing = 0
        self.layer = self.iface.activeLayer()
        self.lastFeatureId = None
        self.selectedFeature = None
        self.rubberBand = None
        self.newFeatures = None

    def setTool(self):
        self.canvas.setMapTool(self)

    def setDistanceDialog(self, isComplexPolygon):
        self.dstDlg = DuplicateDistanceDialog(isComplexPolygon)
        self.dstDlg.previewButton.clicked.connect(self.dstPreview)
        self.dstDlg.okButton.clicked.connect(self.dstOk)
        self.dstDlg.cancelButton.clicked.connect(self.dstCancel)

    def setAttributesDialog(self, fields, attributes):
        self.attDlg = DuplicateAttributesDialog(fields, attributes)
        self.attDlg.okButton.clicked.connect(self.attOk)
        self.attDlg.cancelButton.clicked.connect(self.attCancel)

    def dstCancel(self):
        self.dstDlg.close()
        self.isEditing = 0
        self.canvas.scene().removeItem(self.rubberBand)
        self.rubberBand = None
        self.layer.removeSelection()

    def attCancel(self):
        self.attDlg.close()
        self.isEditing = 0
        self.canvas.scene().removeItem(self.rubberBand)
        self.rubberBand = None
        self.layer.removeSelection()

    @staticmethod
    def angle(point1, point2):
        return atan2(point2.y()-point1.y(), point2.x()-point1.x())

    @staticmethod
    def newPoint(angle, point, distance):
        x = point.x() + cos(angle)*distance
        y = point.y() + sin(angle)*distance
        return QgsPoint(x,y)

    def dstPreview(self):
        if self.rubberBand:
            self.canvas.scene().removeItem(self.rubberBand)
            self.rubberBand = None
        if self.dstDlg.distanceEdit.text():
            distance = float(self.dstDlg.distanceEdit.text())
            if self.layer.wkbType() == QGis.WKBPolygon:
                self.polygonPreview(distance)
            else:
                self.linePreview(distance)
            color = QColor("red")
            color.setAlphaF(0.78)
            self.rubberBand.setWidth(2)
            self.rubberBand.setColor(color)
            self.rubberBand.setLineStyle(Qt.DotLine)
            self.rubberBand.show()

    def linePreview(self, distance):
        points = self.selectedFeature.geometry().asPolyline()
        self.newFeatures = []
        self.rubberBand = QgsRubberBand(self.canvas, QGis.Line)
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
            self.newFeatures.append(self.newPoint(angle, points[pos], dist))
        self.rubberBand.setToGeometry(QgsGeometry.fromPolyline(self.newFeatures), None)

    def polygonPreview(self, distance):
        self.rubberBand = QgsRubberBand(self.canvas, QGis.Polygon)
        lines = self.selectedFeature.geometry().asPolygon()
        self.newFeatures = []
        nb = 0
        for points in lines:
            newPoints = []
            if nb == 1:
                if self.dstDlg.direction_button_group.checkedId() == 1:
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
                self.newFeatures.append(newPoints)
            if nb == 0:
                self.rubberBand.setToGeometry(QgsGeometry.fromPolyline(newPoints), None)
            else:
                self.rubberBand.addGeometry(QgsGeometry.fromPolyline(newPoints), None)
            nb += 1

    def dstOk(self):
        self.dstDlg.close()
        self.setAttributesDialog(self.layer.pendingFields(), self.selectedFeature.attributes())
        self.attDlg.show()

    def attOk(self):
        self.attDlg.close()
        self.canvas.scene().removeItem(self.rubberBand)
        self.rubberBand = None
        self.layer.startEditing()
        if self.layer.wkbType() == QGis.WKBPolygon:
            geometry = QgsGeometry.fromPolygon(self.newFeatures)
        else:
            geometry = QgsGeometry.fromPolyline(self.newFeatures)
        if not geometry.isGeosValid():
            print "bad bad geometry"
        else:
            print "good geometry"
        feature = QgsFeature(self.layer.pendingFields())
        feature.setGeometry(geometry)
        feature.setAttributes(self.attDlg.getAttributes())
        self.layer.addFeature(feature)
        self.layer.updateExtents()
        self.layer.commitChanges()
        self.isEditing = 0
        self.layer.removeSelection()

    def canvasMoveEvent(self, event):
        if not self.isEditing:
            self.layer = self.iface.activeLayer()
            if QGis is not None and self.layer is not None and (self.layer.wkbType() is not None) and (self.layer.wkbType() == QGis.WKBLineString or self.layer.wkbType() == QGis.WKBPolygon):
                f = self.findFeatureAt(event.pos())
                if f and self.lastFeatureId != f.id():
                    self.lastFeatureId = f.id()
                    self.layer.setSelectedFeatures([f.id()])
                if not f:
                    self.layer.removeSelection()
                    self.lastFeatureId = None

    def canvasReleaseEvent(self, event):
        if self.layer and (self.layer.wkbType() is not None) and (self.layer.wkbType() == QGis.WKBLineString or self.layer.wkbType() == QGis.WKBPolygon):
            found_features = self.layer.selectedFeatures()
            if len(found_features) > 0:
                if len(found_features) < 1:
                    self.iface.messageBar().pushMessage(u"Une seule feature à la fois", level=QgsMessageBar.INFO)
                    return
                self.selectedFeature = found_features[0]
                self.isEditing = 1
                if (self.layer.wkbType() == QGis.WKBPolygon) and (len(self.selectedFeature.geometry().asPolygon()) > 1):
                    self.setDistanceDialog(True)
                else:
                    self.setDistanceDialog(False)
                self.dstDlg.distanceEdit.setText("5.0")
                self.dstDlg.show()

    def findFeatureAt(self, pos):
        mapPt,layerPt = self.transformCoordinates(pos)
        tolerance = self.calcTolerance(pos)
        searchRect = QgsRectangle(layerPt.x() - tolerance, layerPt.y() - tolerance, layerPt.x() + tolerance, layerPt.y() + tolerance)
        request = QgsFeatureRequest()
        request.setFilterRect(searchRect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)
        for feature in self.layer.getFeatures(request):
            return feature
        return None

    def transformCoordinates(self, screenPt):
        return self.toMapCoordinates(screenPt), self.toLayerCoordinates(self.layer, screenPt)

    def calcTolerance(self, pos):
        pt1 = QPoint(pos.x(), pos.y())
        pt2 = QPoint(pos.x() + 10, pos.y())
        mapPt1, layerPt1 = self.transformCoordinates(pt1)
        mapPt2, layerPt2 = self.transformCoordinates(pt2)
        tolerance = layerPt2.x() - layerPt1.x()
        return tolerance