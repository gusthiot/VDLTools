# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from math import *

from duplicate_dialog import DuplicateDialog



class DuplicateTool(QgsMapToolIdentify):

    def __init__(self, iface):
        QgsMapToolIdentify.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.dlg = DuplicateDialog()
        self.icon_path = ':/plugins/VDLTools/tools/duplicate_icon.png'
        self.text = 'Duplicate a feature'
        self.dlg.previewButton.clicked.connect(self.preview)
        self.dlg.okButton.clicked.connect(self.ok)
        self.dlg.cancelButton.clicked.connect(self.cancel)
        self.dlg.distanceEdit.setValidator(QDoubleValidator(-1000, 1000, 2, self))
        self.setCursor(Qt.ArrowCursor)
        self.isEditing = 0
        self.layer = self.iface.activeLayer()
        self.lastFeatureId = None
        self.selectedFeature = None
        self.rubberBand = None
        self.newPoints = None

    def setTool(self):
        self.canvas.setMapTool(self)


    def cancel(self):
        self.dlg.close()
        self.isEditing = 0
        self.canvas.scene().removeItem(self.rubberBand)
        self.rubberBand = None
        self.layer.removeSelection()

    def angle(self, point1, point2):
        return atan2(point2.y()-point1.y(), point2.x()-point1.x())

    def newPoint(self, angle, point, distance):
        x = point.x() + cos(angle)*distance
        y = point.y() + sin(angle)*distance
        return QgsPoint(x,y)

    def preview(self):
        if self.rubberBand:
            self.canvas.scene().removeItem(self.rubberBand)
            self.rubberBand = None
        if self.dlg.distanceEdit.text():
            distance = float(self.dlg.distanceEdit.text())
            points = self.selectedFeature.geometry().asPolyline()
            self.newPoints = []
            self.rubberBand = QgsRubberBand(self.canvas, False)
            for pos in range(0, len(points)):
                if pos == 0:
                    angle = self.angle(points[pos],points[pos+1]) + pi/2
                    dist = distance
                elif pos == (len(points)-1):
                    angle = self.angle(points[pos-1],points[pos]) + pi/2
                    dist = distance
                else:
                    angle1 = self.angle(points[pos-1],points[pos])
                    angle2 = self.angle(points[pos],points[pos+1])
                    angle = float(pi + angle1 + angle2)/2
                    dist = float(distance)/sin(float(pi + angle1 - angle2)/2)
                self.newPoints.append(self.newPoint(angle,points[pos],dist))
            self.rubberBand.setToGeometry(QgsGeometry.fromPolyline(self.newPoints), None)
            color = QColor("red")
            color.setAlphaF(0.78)
            self.rubberBand.setWidth(2)
            self.rubberBand.setColor(color)
            self.rubberBand.setLineStyle(Qt.DotLine)
            self.rubberBand.show()

    def ok(self):
        self.canvas.scene().removeItem(self.rubberBand)
        self.rubberBand = None
        self.layer.startEditing()
        geometry = QgsGeometry.fromPolyline(self.newPoints)
        feature = QgsFeature()
        feature.setGeometry(geometry)
        self.layer.addFeature(feature)
        self.layer.updateExtents()
        self.layer.commitChanges()
        self.isEditing = 0
        self.layer.removeSelection()
        self.dlg.close()

    def canvasMoveEvent(self, event):
        if not self.isEditing:
            if self.layer and self.layer.wkbType() == QGis.WKBLineString:
                f = self.findFeatureAt(event.pos())
                if f and self.lastFeatureId != f.id():
                    self.lastFeatureId = f.id()
                    self.layer.setSelectedFeatures([f.id()])
                if not f:
                    self.layer.removeSelection()
                    self.lastFeatureId = None

    def canvasReleaseEvent(self, event):
        if self.layer and self.layer.wkbType() == QGis.WKBLineString:
            found_features = self.identify(event.x(), event.y(), self.TopDownStopAtFirst, self.VectorLayer)
            if len(found_features) > 0:
                if len(found_features) < 1:
                    self.iface.messageBar().pushMessage(u"Une seule feature à la fois", level=QgsMessageBar.INFO)
                    return
                self.selectedFeature = found_features[0].mFeature
                self.isEditing = 1
                self.dlg.distanceEdit.setText("5.0")
                self.dlg.show()

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