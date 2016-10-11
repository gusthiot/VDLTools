# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-04-13
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
from math import (cos,
                  sin,
                  pi)
from PyQt4.QtCore import (Qt,
                          QCoreApplication)
from PyQt4.QtGui import QColor
from qgis.core import (QgsGeometry,
                       QgsPointV2,
                       QgsCircularStringV2,
                       QgsFeature,
                       QGis,
                       QgsMapLayerRegistry,
                       QgsVectorLayer)
from qgis.gui import (QgsMapTool,
                      QgsRubberBand)
from ..ui.intersect_distance_dialog import IntersectDistanceDialog
from ..core.finder import Finder


class IntersectTool(QgsMapTool):

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.__canvas = iface.mapCanvas()
        self.__icon_path = ':/plugins/VDLTools/icons/intersect_icon.png'
        self.__text = QCoreApplication.translate("VDLTools","From intersection")
        self.setCursor(Qt.ArrowCursor)
        self.__lineLayerID = None
        self.__pointLayerID = None
        self.__counter = 0
        self.__rubber = None
        self.__ownSettings = None
        self.__isEditing = 0

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

    def setTool(self):
        """
        To set the current tool as this one
        """
        self.__canvas.setMapTool(self)

    def setOwnSettings(self, settings):
        """
        To set the settings
        :param settings: income settings
        """
        self.__ownSettings = settings

    def __setDistanceDialog(self, mapPoint):
        """
        To create an Intersect Distance Dialog
        :param mapPoint: radius of the circle
        """
        self.__dstDlg = IntersectDistanceDialog(mapPoint)
        self.__dstDlg.okButton().clicked.connect(self.__onDstOk)
        self.__dstDlg.cancelButton().clicked.connect(self.__onDstCancel)
        self.__dstDlg.observation().setValue(6.0)
        self.__dstDlg.observation().selectAll()
        self.__dstDlg.show()

    def __onDstOk(self):
        """
        When the Ok button in Intersect Distance Dialog is pushed
        """
        self.__rubber.reset()
        observation = float(self.__dstDlg.observation().text())
        circle = QgsCircularStringV2()
        x = self.__dstDlg.mapPoint().x()
        y = self.__dstDlg.mapPoint().y()
        circle.setPoints([QgsPointV2(x + observation * cos(pi / 180 * a), y + observation * sin(pi / 180 * a))
                          for a in range(0, 361, 90)])
        lineLayer = self.__lineLayer()
        lineLayer.startEditing()
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry(circle))
        fields = lineLayer.pendingFields()
        feature.setFields(fields)
        fieldsNames = [fields.at(pos).name() for pos in range(fields.count())]
        if "distance" in fieldsNames:
            feature.setAttribute("distance", observation)
        if "x" in fieldsNames:
            feature.setAttribute("x", self.__dstDlg.mapPoint().x())
        if "y" in fieldsNames:
            feature.setAttribute("y", self.__dstDlg.mapPoint().y())
        lineLayer.addFeature(feature)
        lineLayer.updateExtents()
        lineLayer.commitChanges()

        # center
        pointLayer = self.__pointLayer()
        pointLayer.startEditing()
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry().fromPoint(self.__dstDlg.mapPoint()))
        pointLayer.addFeature(feature)
        pointLayer.updateExtents()
        pointLayer.commitChanges()

        self.__isEditing = False
        self.__dstDlg.close()

    def __onDstCancel(self):
        """
        When the Cancel button in Intersect Distance Dialog is pushed
        """
        self.__dstDlg.close()
        self.__rubber.reset()
        self.__isEditing = False

    def activate(self):
        """
        When the action is selected
        """
        QgsMapTool.activate(self)
        self.__rubber = QgsRubberBand(self.__canvas, QGis.Point)
        color = QColor("red")
        color.setAlphaF(0.78)
        self.__rubber.setColor(color)
        self.__rubber.setIcon(4)
        self.__rubber.setIconSize(20)
        self.__rubber.setWidth(2)

    def deactivate(self):
        """
        When the action is deselected
        """
        self.__rubber.reset()
        QgsMapTool.deactivate(self)

    def canvasMoveEvent(self, mouseEvent):
        """
        When the mouse is moved
        :param event: mouse event
        """
        if not self.__isEditing:
            self.__rubber.reset()
            match = Finder.snap(mouseEvent.mapPoint(), self.__canvas)
            if match.hasVertex() or match.hasEdge():
                point = match.point()
                if match.hasVertex():
                    if match.layer():
                        self.__rubber.setIcon(4)
                    else:
                        self.__rubber.setIcon(1)
                if match.hasEdge():
                    intersection = Finder.snapCurvedIntersections(match.point(), self.__canvas, self)
                    if intersection:
                        self.__rubber.setIcon(1)
                        point = intersection
                    else:
                        self.__rubber.setIcon(3)
                self.__rubber.setToGeometry(QgsGeometry().fromPoint(point), None)

    def canvasReleaseEvent(self, mouseEvent):
        """
        When the mouse is clicked
        :param event: mouse event
        """
        if mouseEvent.button() != Qt.LeftButton:
            return
        match = Finder.snap(mouseEvent.mapPoint(), self.__canvas)
        if match.hasVertex() or match.hasEdge():
            point = match.point()
            intersection = Finder.snapCurvedIntersections(match.point(), self.__canvas, self)
            if intersection:
                point = intersection
            self.__isEditing = True
            self.__setDistanceDialog(point)

    def __lineLayer(self):
        """
        To get the line layer to create the circle
        :return: a line layer
        """
        if self.__ownSettings is not None:
            if self.__ownSettings.linesLayer() is not None:
                layer = self.__ownSettings.linesLayer()
                self.__lineLayerID = layer.id()
                return layer
        layer = QgsMapLayerRegistry.instance().mapLayer(self.__lineLayerID)
        if layer is None:
            epsg = self.__iface.mapCanvas().mapRenderer().destinationCrs().authid()
            layer = QgsVectorLayer("LineString?crs=%s&index=yes&field=distance:double&field=x:double&field=y:double"
                                   % epsg, "Memory Lines", "memory")
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            layer.layerDeleted.connect(self.__lineLayerDeleted)
            self.__lineLayerID = layer.id()
            if self.__ownSettings is not None:
                self.__ownSettings.setLinesLayer(layer)
        else:
            self.__iface.legendInterface().setLayerVisible(layer, True)
        return layer

    def __lineLayerDeleted(self):
        """
        To deselect the line layer when it is deleted
        """
        self.lineLayerID = None

    def __pointLayer(self):
        """
        To get the point layer to create the center
        :return: a point layer
        """
        if self.__ownSettings is not None:
            if self.__ownSettings.pointsLayer() is not None:
                layer = self.__ownSettings.pointsLayer()
                self.__pointLayerID = layer.id()
                return layer
        layer = QgsMapLayerRegistry.instance().mapLayer(self.__pointLayerID)
        if layer is None:
            epsg = self.__iface.mapCanvas().mapRenderer().destinationCrs().authid()
            layer = QgsVectorLayer("Point?crs=%s&index=yes" % epsg, "Memory Points", "memory")
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            layer.layerDeleted.connect(self.__pointLayerDeleted)
            self.__pointLayerID = layer.id()
            if self.__ownSettings is not None:
                self.__ownSettings.setPointsLayer(layer)
        else:
            self.__iface.legendInterface().setLayerVisible(layer, True)
        return layer

    def __pointLayerDeleted(self):
        """
        To deselect the point layer when it is deleted
        :return:
        """
        self.__pointLayerID = None
