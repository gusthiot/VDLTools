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
from builtins import range
from math import (cos,
                  sin,
                  pi)
from qgis.PyQt.QtCore import (Qt,
                              QCoreApplication)
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsGeometry,
                       QgsWkbTypes,
                       QgsPoint,
                       QgsCircularString,
                       QgsFeature,
                       QgsProject,
                       QgsVectorLayer)
from qgis.gui import (QgsMapTool,
                      QgsRubberBand)
from ..ui.intersect_distance_dialog import IntersectDistanceDialog
from ..core.finder import Finder


class IntersectTool(QgsMapTool):
    """
    Map tool class to create temporary circle, with center point
    """

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.icon_path = ':/plugins/VDLTools/icons/intersect_icon.png'
        self.text = QCoreApplication.translate("VDLTools", "From intersection")
        self.setCursor(Qt.ArrowCursor)
        self.__lineLayerID = None
        self.__pointLayerID = None
        self.__rubber = None
        self.ownSettings = None
        self.__isEditing = False
        self.__distance = 0

    def setTool(self):
        """
        To set the current tool as this one
        """
        self.canvas().setMapTool(self)

    def activate(self):
        """
        When the action is selected
        """
        QgsMapTool.activate(self)
        self.__rubber = QgsRubberBand(self.canvas(), QgsWkbTypes.PointGeometry)
        color = QColor("red")
        color.setAlphaF(0.78)
        self.__rubber.setColor(color)
        self.__rubber.setIcon(4)
        self.__rubber.setIconSize(20)
        self.__rubber.setWidth(2)
        self.__distance = 6.0

    def deactivate(self):
        """
        When the action is deselected
        """
        self.__cancel()
        self.__rubber = None
        QgsMapTool.deactivate(self)

    def __cancel(self):
        """
        To cancel used variables
        """
        if self.__rubber is not None:
            self.__rubber.reset()
        self.__isEditing = False

    def __setDistanceDialog(self, mapPoint):
        """
        To create an Intersect Distance Dialog
        :param mapPoint: radius of the circle
        """
        self.__dstDlg = IntersectDistanceDialog(mapPoint)
        self.__dstDlg.rejected.connect(self.__cancel)
        self.__dstDlg.okButton().clicked.connect(self.__onDstOk)
        self.__dstDlg.cancelButton().clicked.connect(self.__onDstCancel)
        self.__dstDlg.observation().setValue(self.__distance)
        self.__dstDlg.observation().selectAll()
        self.__dstDlg.show()

    def __onDstOk(self):
        """
        When the Ok button in Intersect Distance Dialog is pushed
        """
        self.__distance = float(self.__dstDlg.observation().text())
        circle = QgsCircularString()
        x = self.__dstDlg.mapPoint().x()
        y = self.__dstDlg.mapPoint().y()
        circle.setPoints([QgsPoint(x + self.__distance * cos(pi / 180 * a), y + self.__distance * sin(pi / 180 * a))
                          for a in range(0, 361, 90)])
        lineLayer = self.__lineLayer()
        lineLayer.startEditing()
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry(circle))
        fields = lineLayer.fields()
        feature.setFields(fields)
        fieldsNames = [fields.at(pos).name() for pos in range(fields.count())]
        if "distance" in fieldsNames:
            feature.setAttribute("distance", self.__distance)
        if "x" in fieldsNames:
            feature.setAttribute("x", x)
        if "y" in fieldsNames:
            feature.setAttribute("y", y)
        lineLayer.addFeature(feature)
        # lineLayer.updateExtents()
        lineLayer.commitChanges()

        # center
        pointLayer = self.__pointLayer()
        pointLayer.startEditing()
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry().fromPointXY(self.__dstDlg.mapPoint()))
        feature.setFields(pointLayer.fields())
        pointLayer.addFeature(feature)
        pointLayer.commitChanges()

        self.__dstDlg.accept()
        self.__cancel()

    def __onDstCancel(self):
        """
        When the Cancel button in Intersect Distance Dialog is pushed
        """
        self.__dstDlg.reject()

    def canvasMoveEvent(self, mouseEvent):
        """
        When the mouse is moved
        :param mouseEvent: mouse event
        """
        if not self.__isEditing:
            self.__rubber.reset()
            match = self.canvas().snappingUtils().snapToMap(mouseEvent.mapPoint())
            if match.hasVertex() or match.hasEdge():
                point = match.point()
                if match.hasVertex():
                    if match.layer():
                        self.__rubber.setIcon(4)
                    else:
                        self.__rubber.setIcon(1)
                if match.hasEdge():
                    self.__rubber.setIcon(3)
                self.__rubber.setToGeometry(QgsGeometry().fromPointXY(point), None)

    def canvasReleaseEvent(self, mouseEvent):
        """
        When the mouse is clicked
        :param mouseEvent: mouse event
        """
        if mouseEvent.button() != Qt.LeftButton:
            return
        match = self.canvas().snappingUtils().snapToMap(mouseEvent.mapPoint())
        if match.hasVertex() or match.hasEdge():
            point = match.point()
            self.__isEditing = True
            self.__setDistanceDialog(point)

    def __lineLayer(self):
        """
        To get the line layer to create the circle
        :return: a line layer
        """
        if self.ownSettings is not None:
            if self.ownSettings.linesLayer is not None:
                layer = self.ownSettings.linesLayer
                self.__lineLayerID = layer.id()
                return layer
        layer = QgsProject.instance().mapLayer(self.__lineLayerID)
        if layer is None:
            epsg = self.canvas().mapSettings().destinationCrs().authid()
            layer = QgsVectorLayer("LineString?crs=%s&index=yes&field=distance:double&field=x:double&field=y:double"
                                   % epsg, "Memory Lines", "memory")
            QgsProject.instance().addMapLayer(layer)
            layer.destroyed.connect(self.__lineLayerDeleted)
            self.__lineLayerID = layer.id()
            if self.ownSettings is not None:
                self.ownSettings.linesLayer = layer
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
        if self.ownSettings is not None:
            if self.ownSettings.pointsLayer is not None:
                layer = self.ownSettings.pointsLayer
                self.__pointLayerID = layer.id()
                return layer
        layer = QgsProject.instance().mapLayer(self.__pointLayerID)
        if layer is None:
            epsg = self.canvas().mapSettings().destinationCrs().authid()
            layer = QgsVectorLayer("Point?crs=%s&index=yes" % epsg, "Memory Points", "memory")
            QgsProject.instance().addMapLayer(layer)
            layer.destroyed.connect(self.__pointLayerDeleted)
            self.__pointLayerID = layer.id()
            if self.ownSettings is not None:
                self.ownSettings.pointsLayer = layer
        else:
            self.__iface.legendInterface().setLayerVisible(layer, True)
        return layer

    def __pointLayerDeleted(self):
        """
        To deselect the point layer when it is deleted
        """
        self.__pointLayerID = None
