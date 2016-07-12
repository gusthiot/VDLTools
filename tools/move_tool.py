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
        self.__layer = None
        self.__lastFeatureId = None
        self.__selectedFeature = None
        self.__rubberBand = None
        self.__newFeature = None
        self.__oldTool = None
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

    def __pointPreview(self, position):
        point_v2 = GeometryV2.asPointV2(self.__selectedFeature.geometry())
        self.__newFeature = QgsPointV2(position.x(), position.y())
        self.__newFeature.addZValue(point_v2.z())
        self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Point)
        self.__rubberBand.setToGeometry(QgsGeometry(self.__newFeature.clone()), None)

    def __linePreview(self, position):
        line_v2 = GeometryV2.asLineStringV2(self.__selectedFeature.geometry())
        vertex = line_v2.pointN(self.__selectedVertex)
        dx = vertex.x() - position.x()
        dy = vertex.y() - position.y()
        self.__newFeature = QgsLineStringV2()
        self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Line)
        for pos in xrange(line_v2.numPoints()):
            x = line_v2.pointN(pos).x() - dx
            y = line_v2.pointN(pos).y() - dy
            pt = QgsPointV2(x, y)
            pt.addZValue(line_v2.pointN(pos).z())
            self.__newFeature.addVertex(pt)
        self.__rubberBand.setToGeometry(QgsGeometry(self.__newFeature.clone()), None)

    def __polygonPreview(self, position):
        self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Polygon)
        polygon_v2 = GeometryV2.asPolygonV2(self.__selectedFeature.geometry())
        self.__newFeature = QgsPolygonV2()
        line_v2 = self.__newLine(polygon_v2.exteriorRing())
        self.__newFeature.setExteriorRing(line_v2)
        self.__rubberBand.setToGeometry(QgsGeometry(line_v2.clone()), None)
        for num in xrange(polygon_v2.numInteriorRings()):
            line_v2 = self.__newLine(polygon_v2.interiorRing(num))
            self.__newFeature.addInteriorRing(line_v2)
            self.__rubberBand.addGeometry(QgsGeometry(line_v2.clone()), None)

    def __newLine(self, curve_v2):
        new_line_v2 = QgsLineStringV2()
        line_v2 = curve_v2.curveToLine()
        for pos in xrange(line_v2.numPoints()):
            pass
            # if pos == 0:
            #     pos1 = curve_v2.numPoints() - 2
            # else:
            #     pos1 = pos - 1
            # pos2 = pos
            # if pos == (curve_v2.numPoints() - 1):
            #     pos3 = 1
            # else:
            #     pos3 = pos + 1
            # angle1 = self.angle(line_v2.pointN(pos1), line_v2.pointN(pos2))
            # angle2 = self.angle(line_v2.pointN(pos), line_v2.pointN(pos3))
            # angle = float(pi + angle1 + angle2) / 2
            # dist = float(distance) / sin(float(pi + angle1 - angle2) / 2)
            # new_line_v2.addVertex(self.newPoint(angle, line_v2.pointN(pos), dist))
        return new_line_v2

    def __ok(self):
        self.__preview()
        self.__canvas.scene().removeItem(self.__rubberBand)
        if self.__layer.geometryType() == QGis.Polygon:
            geometry = QgsGeometry(self.__newFeature)
        else:
            geometry = QgsGeometry(self.__newFeature)
        if not geometry.isGeosValid():
            print "geometry problem"
        self.__rubberBand = None
        feature = QgsFeature(self.__layer.pendingFields())
        feature.setGeometry(geometry)
        feature.setAttributes(self.__selectedFeature.attributes())
        self.__layer.addFeature(feature)
        self.__layer.updateExtents()
        self.__isEditing = 0
        self.__layer.removeSelection()

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
                self.__canvas.scene().removeItem(self.__rubberBand)
                self.__rubberBand = None
            if self.__dstDlg.distanceEditText():
                if self.__layer.geometryType() == QGis.Polygon:
                    self.__polygonPreview(event.pos())
                elif self.__layer.geometryType() == QGis.Line:
                    self.__linePreview(event.pos())
                else:
                    self.__pointPreview(event.pos())
            color = QColor("red")
            color.setAlphaF(0.78)
            self.__rubberBand.setColor(color)
            if self.__layer.geometryType() != QGis.Point:
                self.__rubberBand.setWidth(2)
                self.__rubberBand.setLineStyle(Qt.DotLine)
            else:
                self.__rubberBand.setIcon(4)
                self.__rubberBand.setIconSize(20)
            self.__rubberBand.show()

    def canvasReleaseEvent(self, event):
        if not self.__isEditing and not self.__findVertex:
            found_features = self.__layer.selectedFeatures()
            if len(found_features) > 0:
                if len(found_features) < 1:
                    self.__iface.messageBar().pushMessage(u"Une seule feature à la fois", level=QgsMessageBar.INFO)
                    return
                self.__selectedFeature = found_features[0]
                # self.__isEditing = 1
                print self.__layer.geometryType()
                if self.__layer.geometryType() != QGis.Point:
                    self.__findVertex = 1
                    self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Point)
                else:
                    self.__onMove = 1

        elif self.__findVertex:
            self.__findVertex = 0
            closest = self.__selectedFeature.geometry().closestVertex(event.mapPoint())
            self.__selectedVertex = closest[1]
            self.__rubberBand = QgsRubberBand(self.__canvas, QGis.Point)
            self.__onMove = 1



