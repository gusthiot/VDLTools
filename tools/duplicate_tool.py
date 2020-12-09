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
from qgis.PyQt.QtCore import (Qt,
                              QCoreApplication)
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsEditFormConfig,
                       QgsTolerance,
                       QgsWkbTypes,
                       QgsGeometry,
                       QgsCircularString,
                       QgsLineString,
                       QgsFeature,
                       QgsDataSourceUri,
                       QgsCurvePolygon,
                       QgsPoint,
                       QgsMapLayer)
from qgis.gui import (QgsMapTool,
                      QgsRubberBand,
                      QgsMessageBar)
from ..ui.duplicate_distance_dialog import DuplicateDistanceDialog
from ..core.finder import Finder
from ..core.signal import Signal


class DuplicateTool(QgsMapTool):
    """
    Map tool class to duplicate an object
    """

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.icon_path = ':/plugins/VDLTools/icons/duplicate_icon.png'
        self.text = QCoreApplication.translate("VDLTools", "Duplicate a feature")
        self.setCursor(Qt.ArrowCursor)
        self.__isEditing = False
        self.__layer = None
        self.__lastFeatureId = None
        self.__selectedFeature = None
        self.__rubberBand = None
        self.__newFeature = None
        self.__dstDlg = None

    def deactivate(self):
        """
        When the action is deselected
        """
        self.__cancel()
        QgsMapTool.deactivate(self)

    def startEditing(self):
        """
        To set the action as enable, as the layer is editable
        """
        self.action().setEnabled(True)
        Signal.safelyDisconnect(self.__layer.editingStarted, self.startEditing)
        self.__layer.editingStopped.connect(self.stopEditing)

    def stopEditing(self):
        """
        To set the action as disable, as the layer is not editable
        """
        self.action().setEnabled(False)
        Signal.safelyDisconnect(self.__layer.editingStopped, self.stopEditing)
        self.__layer.editingStarted.connect(self.startEditing)
        if self.canvas().mapTool() == self:
            self.__iface.actionPan().trigger()

    def setTool(self):
        """
        To set the current tool as this one
        """
        self.canvas().setMapTool(self)

    def __cancel(self):
        """
        To cancel used variables
        """
        self.__isEditing = False
        if self.__rubberBand is not None:
            self.canvas().scene().removeItem(self.__rubberBand)
            self.__rubberBand.reset()
            self.__rubberBand = None
        self.__dstDlg = None
        self.__newFeature = None
        self.__lastFeatureId = None
        self.__selectedFeature = None
        self.__layer.removeSelection()

    def __removeLayer(self):
        """
        To remove the current working layer
        """
        if self.__layer is not None:
            if self.__layer.isEditable():
                Signal.safelyDisconnect(self.__layer.editingStopped, self.stopEditing)
            else:
                Signal.safelyDisconnect(self.__layer.editingStarted, self.startEditing)
            self.__layer = None

    def setEnable(self, layer):
        """
        To check if we can enable the action for the selected layer
        :param layer: selected layer
        """
        types = [QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry]
        if layer is not None and layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() in types:
            if layer == self.__layer:
                return

            if self.__layer is not None:
                if self.__layer.isEditable():
                    Signal.safelyDisconnect(self.__layer.editingStopped, self.stopEditing)
                else:
                    Signal.safelyDisconnect(self.__layer.editingStarted, self.startEditing)
            self.__layer = layer
            if self.__layer.isEditable():
                self.action().setEnabled(True)
                self.__layer.editingStopped.connect(self.stopEditing)
            else:
                self.action().setEnabled(False)
                self.__layer.editingStarted.connect(self.startEditing)
                if self.canvas().mapTool() == self:
                    self.__iface.actionPan().trigger()
            return

        if self.canvas().mapTool() == self:
            self.__iface.actionPan().trigger()
        self.action().setEnabled(False)
        self.__removeLayer()

    def __setDistanceDialog(self, isComplexPolygon):
        """
        To create a Duplicate Distance Dialog
        :param isComplexPolygon: for a polygon, if it has interior ring(s)
        """
        self.__dstDlg = DuplicateDistanceDialog(isComplexPolygon)
        self.__dstDlg.rejected.connect(self.__cancel)
        self.__dstDlg.previewButton().clicked.connect(self.__onDstPreview)
        self.__dstDlg.okButton().clicked.connect(self.__onDstOk)
        self.__dstDlg.cancelButton().clicked.connect(self.__onDstCancel)
        self.__dstDlg.directionCheck().stateChanged.connect(self.__onDstPreview)

    def __onDstCancel(self):
        """
        When the Cancel button in Duplicate Distance Dialog is pushed
        """
        self.__dstDlg.reject()

    @staticmethod
    def __newPoint(angle, point, distance):
        """
        To create a new point at a certain distance and certain azimut from another point
        :param angle: the azimut
        :param point: the reference point
        :param distance: the distance
        :return: the new QgsPoint (with same elevation than parameter point)
        """
        x = point.x() + cos(angle)*distance
        y = point.y() + sin(angle)*distance
        pt = QgsPoint(x, y)
        pt.addZValue(point.z())
        return pt

    def __onDstPreview(self):
        """
        When the Preview button in Duplicate Distance Dialog is pushed
        """
        if self.__rubberBand is not None:
            self.canvas().scene().removeItem(self.__rubberBand)
            self.__rubberBand = None
        if self.__dstDlg.distanceEdit().text() is not None:
            distance = float(self.__dstDlg.distanceEdit().text())
            if self.__dstDlg.directionCheck().checkState():
                distance = -distance
            if self.__layer.geometryType() == QgsWkbTypes.PolygonGeometry:
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
        """
        To create the preview (rubberBand) of the duplicate line at a certain distance
        :param distance: the given distance
        """
        self.__rubberBand = QgsRubberBand(self.canvas(), QgsWkbTypes.LineGeometry)
        line = self.__selectedFeature.geometry().constGet().clone()
        self.__newFeature = self.__newLine(line, distance)
        self.__rubberBand.setToGeometry(QgsGeometry(self.__newFeature.clone()), None)

    def __newLine(self, line, distance):
        """
        To duplicate a line at a given distance
        :param line: the line to duplicate
        :param distance: the given distance
        :return: the new line
        """
        new_line = QgsLineString()
        points = []
        for pos in range(line.numPoints()):
            if pos == 0:
                angle = self.angle(line.pointN(pos), line.pointN(pos + 1)) + pi/2
                dist = distance
            elif pos == (line.numPoints() - 1):
                angle = self.angle(line.pointN(pos - 1), line.pointN(pos)) + pi/2
                dist = distance
            else:
                angle1 = self.angle(line.pointN(pos - 1), line.pointN(pos))
                angle2 = self.angle(line.pointN(pos), line.pointN(pos + 1))
                angle = float(pi + angle1 + angle2)/2
                dist = float(distance) / (sin(float(pi + angle1 - angle2)/2))
            points.append(self.__newPoint(angle, line.pointN(pos), dist))
        new_line.setPoints(points)
        return new_line

    def __polygonPreview(self, distance):
        """
        To create the preview (rubberBand) of the duplicate polygon at a certain distance
        :param distance: the given distance
        """
        self.__rubberBand = QgsRubberBand(self.canvas(), QgsWkbTypes.LineGeometry)
        polygon = self.__selectedFeature.geometry().constGet().clone()
        self.__newFeature = QgsCurvePolygon()
        line = self.__newPolygonLine(polygon.exteriorRing(), distance)
        self.__newFeature.setExteriorRing(line)
        self.__rubberBand.setToGeometry(QgsGeometry(line.clone()), None)
        for num in range(polygon.numInteriorRings()):
            if self.__dstDlg.isInverted():
                distance = -distance
            line = self.__newPolygonLine(polygon.interiorRing(num), distance)
            self.__newFeature.addInteriorRing(line)
            # self.__rubberBand.addGeometry(QgsGeometry(line_v2.curveToLine()), None)
            self.__rubberBand.addGeometry(line, None)

    def __newPolygonLine(self, polygon, distance):
        """
        To create a duplicate curve for a polygon curves
        :param polygon: curve to duplicate
        :param distance: distance where to
        :return: new duplicate curve
        """
        new_line = QgsLineString()
        points = []

        for pos in range(polygon.numPoints()):
            if pos == 0:
                pos1 = polygon.numPoints() - 2
            else:
                pos1 = pos - 1
            pos2 = pos
            if pos == (polygon.numPoints() - 1):
                pos3 = 1
            else:
                pos3 = pos + 1
            angle1 = self.angle(polygon.pointN(pos1), polygon.pointN(pos2))
            angle2 = self.angle(polygon.pointN(pos), polygon.pointN(pos3))
            angle = float(pi + angle1 + angle2)/2
            dist = float(distance) / (sin(float(pi + angle1 - angle2)/2))
            points.append(self.__newPoint(angle, polygon.pointN(pos), dist))
        new_line.setPoints(points)
        return new_line

    def __onDstOk(self):
        """
        When the Ok button in Duplicate Distance Dialog is pushed
        """
        self.__onDstPreview()
        self.__dstDlg.accept()
        geometry = QgsGeometry(self.__newFeature)
        if not geometry.isGeosValid():
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "Geos geometry problem"),
                                                  level=QgsMessageBar.CRITICAL, duration=0)
        feature = QgsFeature(self.__layer.fields())
        feature.setGeometry(geometry)
        primaryKey = QgsDataSourceUri(self.__layer.source()).keyColumn()
        for field in self.__selectedFeature.fields():
            if field.name() != primaryKey:
                feature.setAttribute(field.name(), self.__selectedFeature.attribute(field.name()))
        if len(self.__selectedFeature.fields()) > 0 and self.__layer.editFormConfig().suppress() != \
                QgsEditFormConfig.SuppressOn:
            if self.__iface.openFeatureForm(self.__layer, feature):
                self.__layer.addFeature(feature)
        else:
            ok, outs = self.__layer.dataProvider().addFeatures([feature])
        self.__layer.updateExtents()
        self.__cancel()

    def canvasMoveEvent(self, event):
        """
        When the mouse is moved
        :param event: mouse event
        """
        if not self.__isEditing:
            feat = Finder.findClosestFeatureAt(event.mapPoint(), self.__layer, 10, QgsTolerance.Pixels, self)
            if feat is not None and self.__lastFeatureId != feat.id():
                self.__lastFeatureId = feat.id()
                self.__layer.selectByIds([feat.id()])
            if feat is None:
                self.__layer.removeSelection()
                self.__lastFeatureId = None

    def canvasReleaseEvent(self, event):
        """
        When the mouse is clicked
        :param event: mouse event
        """
        found_features = self.__layer.selectedFeatures()
        if len(found_features) > 0:
            if len(found_features) > 1:
                self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "One feature at a time"),
                                                      level=QgsMessageBar.INFO)
                return
            self.__selectedFeature = found_features[0]
            self.__isEditing = True
            if self.__layer.geometryType() == QgsWkbTypes.PolygonGeometry\
                    and len(self.__selectedFeature.geometry().asPolygon()) > 1:
                self.__setDistanceDialog(True)
            else:
                self.__setDistanceDialog(False)
            self.__dstDlg.distanceEdit().setText("5.0")
            self.__dstDlg.distanceEdit().selectAll()
            self.__dstDlg.show()

    def angle(self, point1, point2):
        """
        To calculate the angle of a line between 2 points
        :param point1: first point
        :param point2: second point
        :return: the calculated angle
        """
        return atan2(point2.y() - point1.y(), point2.x() - point1.x())