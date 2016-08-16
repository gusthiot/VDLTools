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
from PyQt4.QtCore import (Qt,
                          QCoreApplication)
from PyQt4.QtGui import QColor
from qgis.core import (QgsPointV2,
                       QgsLineStringV2,
                       QgsPolygonV2,
                       QgsDataSourceURI,
                       QGis,
                       QgsGeometry,
                       QgsFeature,
                       QgsMapLayer)
from qgis.gui import (QgsMapTool,
                      QgsRubberBand,
                      QgsMessageBar)
from ..ui.duplicate_distance_dialog import DuplicateDistanceDialog
from ..core.finder import Finder
from ..core.geometry_v2 import GeometryV2


class DuplicateTool(QgsMapTool):

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.__canvas = iface.mapCanvas()
        self.__icon_path = ':/plugins/VDLTools/icons/duplicate_icon.png'
        self.__text = QCoreApplication.translate("VDLTools","Duplicate a feature")
        self.setCursor(Qt.ArrowCursor)
        self.__isEditing = 0
        self.__layer = None
        self.__lastFeatureId = None
        self.__selectedFeature = None
        self.__rubberBand = None
        self.__newFeature = None
        # self.__oldTool = None

    def icon_path(self):
        """
        To get the icon path
        :return: icon path
        """
        return self.__icon_path

    def text(self):
        """
        To get the menu text
        :return: menu text
        """
        return self.__text

    def toolName(self):
        """
        To get the tool name
        :return: tool name
        """
        return QCoreApplication.translate("VDLTools","Duplicate")

    def startEditing(self):
        """
        To set the action as enable, as the layer is editable
        """
        self.action().setEnabled(True)
        self.__layer.editingStarted.disconnect(self.startEditing)
        self.__layer.editingStopped.connect(self.stopEditing)

    def stopEditing(self):
        """
        To set the action as disable, as the layer is not editable
        """
        self.action().setEnabled(False)
        self.__layer.editingStopped.disconnect(self.stopEditing)
        self.__layer.editingStarted.connect(self.startEditing)
        self.__iface.actionPan().trigger()
        # if self.__canvas.mapTool == self:
            # self.__canvas.setMapTool(self.__oldTool)

    def setTool(self):
        """
        To set the current tool as this one
        """
        # self.__oldTool = self.__canvas.mapTool()
        self.__canvas.setMapTool(self)

    def removeLayer(self):
        """
        To remove the current working layer
        """
        if self.__layer is not None:
            if self.__layer.isEditable():
                self.__layer.editingStopped.disconnect(self.stopEditing)
            else:
                self.__layer.editingStarted.disconnect(self.startEditing)
            self.__layer = None

    def setEnable(self, layer):
        """
        To check if we can enable the action for the selected layer
        :param layer: selected layer
        """
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
                    self.__iface.actionPan().trigger()
                #    self.__canvas.setMapTool(self.__oldTool)
            return
        self.action().setEnabled(False)
        self.removeLayer()

    def __setDistanceDialog(self, isComplexPolygon):
        """
        To create a Duplicate Distance Dialog
        :param isComplexPolygon: for a polygon, if it has interior ring(s)
        """
        self.__dstDlg = DuplicateDistanceDialog(isComplexPolygon)
        self.__dstDlg.previewButton().clicked.connect(self.__onDstPreview)
        self.__dstDlg.okButton().clicked.connect(self.__onDstOk)
        self.__dstDlg.cancelButton().clicked.connect(self.__onDstCancel)

    def __onDstCancel(self):
        """
        When the Cancel button in Duplicate Distance Dialog is pushed
        """
        self.__dstDlg.close()
        self.__isEditing = 0
        self.__canvas.scene().removeItem(self.__rubberBand)
        self.__rubberBand = None
        self.__layer.removeSelection()

    @staticmethod
    def angle(point1, point2):
        """
        To calculate the angle of a line between 2 points
        :param point1: first point
        :param point2: second point
        :return: the calculated angle
        """
        return atan2(point2.y()-point1.y(), point2.x()-point1.x())

    @staticmethod
    def newPoint(angle, point, distance):
        """
        To create a new point at a certain distance and certain azimut from another point
        :param angle: the azimut
        :param point: the reference point
        :param distance: the distance
        :return: the new QgsPoint (with same elevation than parameter point)
        """
        x = point.x() + cos(angle)*distance
        y = point.y() + sin(angle)*distance
        pt = QgsPointV2(x, y)
        pt.addZValue(point.z())
        return pt

    def __onDstPreview(self):
        """
        When the Preview button in Duplicate Distance Dialog is pushed
        """
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

# TODO : newfeature en fonction de curved, puis pareil pour polygon, et pareil pour move
    def __linePreview(self, distance):
        """
        To create the preview (rubberBand) of the duplicate line at a certain distance
        :param distance: the given distance
        """
        line_v2, curved = GeometryV2.asLineV2(self.__selectedFeature.geometry())
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
        """
        To create the preview (rubberBand) of the duplicate polygon at a certain distance
        :param distance: the given distance
        """
        self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Polygon)
        polygon_v2, curved = GeometryV2.asPolygonV2(self.__selectedFeature.geometry())
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
        """
        To create a duplicate curve for a polygon curves
        :param curve_v2: curve to duplicate
        :param distance: distance where to duplicate
        :return: new duplicate curve
        """
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

    def __onDstOk(self):
        """
        When the Ok button in Duplicate Distance Dialog is pushed
        """
        self.__onDstPreview()
        self.__dstDlg.close()
        self.__canvas.scene().removeItem(self.__rubberBand)
        geometry = QgsGeometry(self.__newFeature)
        if not geometry.isGeosValid():
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools","Error"),
                                                  QCoreApplication.translate("VDLTools","Geos geometry problem"),
                                                  level=QgsMessageBar.CRITICAL)
        self.__rubberBand = None
        feature = QgsFeature(self.__layer.pendingFields())
        feature.setGeometry(geometry)
        primaryKey = QgsDataSourceURI(self.__layer.source()).keyColumn()
        for field in self.__selectedFeature.fields():
            if field.name() != primaryKey:
                feature.setAttribute(field.name(), self.__selectedFeature.attribute(field.name()))
        if len(self.__selectedFeature.fields()) > 0:
            self.__iface.openFeatureForm(self.__layer, feature)
        else:
            self.__layer.addFeature(feature)
        self.__layer.updateExtents()
        self.__isEditing = 0
        self.__layer.removeSelection()

    def canvasMoveEvent(self, event):
        """
        When the mouse is moved
        :param event: mouse event
        """
        if not self.__isEditing:
            f = Finder.findClosestFeatureAt(event.pos(), self.__layer, self)
            if f is not None and self.__lastFeatureId != f.id():
                self.__lastFeatureId = f.id()
                self.__layer.setSelectedFeatures([f.id()])
            if f is None:
                self.__layer.removeSelection()
                self.__lastFeatureId = None

    def canvasReleaseEvent(self, event):
        """
        When the mouse is clicked
        :param event: mouse event
        """
        found_features = self.__layer.selectedFeatures()
        if len(found_features) > 0:
            if len(found_features) < 1:
                self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools","One feature at a time"),
                                                      level=QgsMessageBar.INFO)
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
