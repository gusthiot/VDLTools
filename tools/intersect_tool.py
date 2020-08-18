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
from datetime import datetime
from math import (cos,
                  sin,
                  pi)
from qgis.PyQt.QtCore import (Qt,
                              QCoreApplication)
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsGeometry,
                       Qgis,
                       QgsWkbTypes,
                       QgsPoint,
                       QgsCircularString,
                       QgsFeature)
from qgis.gui import (QgsMapTool,
                      QgsRubberBand)
from ..ui.intersect_distance_dialog import IntersectDistanceDialog
from ..core.memory_layers import MemoryLayers


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
        self.__memoryLayers = None
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
        self.__memoryLayers = MemoryLayers(self.__iface, self.ownSettings)

    def deactivate(self):
        """
        When the action is deselected
        """
        self.__cancel()
        self.__rubber = None
        self.__memoryLayers = None
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
        did = datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.__distance = self.__dstDlg.observation().value()
        circle = QgsCircularString()
        x = self.__dstDlg.mapPoint().x()
        y = self.__dstDlg.mapPoint().y()
        circle.setPoints([QgsPoint(x + self.__distance * cos(pi / 180 * a), y + self.__distance * sin(pi / 180 * a))
                          for a in range(0, 361, 90)])
        lineLayer = self.__memoryLayers.lineLayer()
        lineLayer.startEditing()
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry(circle))
        fields = lineLayer.fields()
        feature.setFields(fields)
        fieldsNames = [fields.at(pos).name() for pos in range(fields.count())]
        if "id" in fieldsNames:
            feature.setAttribute("id", did)
        else:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "no 'id' attribute in line layer"),
                level=Qgis.Warning)
        if "type" in fieldsNames:
            feature.setAttribute("type", "distance")
        else:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "no 'type' attribute in line layer"),
                level=Qgis.Warning)
        if "mesure" in fieldsNames:
            feature.setAttribute("mesure", self.__distance)
        else:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "no 'mesure' attribute in line layer"),
                level=Qgis.Warning)
        if "x" in fieldsNames:
            feature.setAttribute("x", x)
        else:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "no 'x' attribute in line layer"),
                level=Qgis.Warning)
        if "y" in fieldsNames:
            feature.setAttribute("y", y)
        else:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "no 'y' attribute in line layer"),
                level=Qgis.Warning)
        ok, outs = lineLayer.dataProvider().addFeatures([feature])
        lineLayer.updateExtents()
        lineLayer.triggerRepaint()
        lineLayer.featureAdded.emit(outs[0].id())  # emit signal so feature is added to snapping index

        # center
        pointLayer = self.__memoryLayers.pointLayer()
        pointLayer.startEditing()
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry().fromPointXY(self.__dstDlg.mapPoint()))
        feature.setFields(pointLayer.fields())
        fieldsNames = [fields.at(pos).name() for pos in range(fields.count())]
        if "id" in fieldsNames:
            feature.setAttribute("id", did)
        else:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "no 'id' attribute in point layer"),
                level=Qgis.Warning)
        ok, outs = pointLayer.dataProvider().addFeatures([feature])
        pointLayer.updateExtents()
        pointLayer.triggerRepaint()
        pointLayer.featureAdded.emit(outs[0].id())  # emit signal so feature is added to snapping index

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
