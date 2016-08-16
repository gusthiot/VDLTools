# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-05-30
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

from qgis.gui import (QgsMapTool,
                      QgsRubberBand,
                      QgsMessageBar)
from qgis.core import (QGis,
                       QgsMapLayer,
                       QgsGeometry,
                       QgsWKBTypes)
from PyQt4.QtCore import (Qt,
                          QCoreApplication)
from PyQt4.QtGui import QColor
from ..core.finder import Finder
from ..core.geometry_v2 import GeometryV2
from ..ui.extrapolate_confirm_dialog import ExtrapolateConfirmDialog


class ExtrapolateTool(QgsMapTool):

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.__iface = iface
        self.__canvas = iface.mapCanvas()
        self.__icon_path = ':/plugins/VDLTools/icons/extrapolate_icon.png'
        self.__text = QCoreApplication.translate("VDLTools",
                                                 "Extrapolate the elevation of a vertex and a "
                                                 "point at the extremity of a line")
        # self.__oldTool = None
        self.__layer = None
        self.setCursor(Qt.ArrowCursor)
        self.__isEditing = False
        self.__lastFeatureId = None
        self.__layerList = None
        self.__lastLayer = None
        self.__rubber = None
        self.__counter = 0
        self.__confDlg = None
        self.__selectedVertex = None
        self.__elevation = None

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
        # self.__oldTool = self.__canvas.mapTool()
        self.__canvas.setMapTool(self)

    def activate(self):
        """
        When the action is selected
        """
        QgsMapTool.activate(self)
        self.__updateList()
        self.__rubber = QgsRubberBand(self.__canvas, QGis.Point)
        color = QColor("red")
        color.setAlphaF(0.78)
        self.__rubber.setColor(color)
        self.__rubber.setIcon(4)
        self.__rubber.setIconSize(20)

    def deactivate(self):
        """
        When the action is deselected
        """
        self.__rubber.reset()
        QgsMapTool.deactivate(self)

    def startEditing(self):
        """
        To set the action as enable, as the layer is editable
        """
        self.action().setEnabled(True)
        self.__canvas.layersChanged.connect(self.__updateList)
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
        #     self.__canvas.setMapTool(self.__oldTool)

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
        if layer is not None\
                and layer.type() == QgsMapLayer.VectorLayer\
                and QGis.fromOldWkbType(layer.wkbType()) == QgsWKBTypes.LineStringZ:

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

    def __updateList(self):
        """
        To update the line layers list that we can use for extrapolation
        """
        self.__layerList = []
        for layer in self.__iface.mapCanvas().layers():
            if layer is not None \
                    and layer.type() == QgsMapLayer.VectorLayer \
                    and QGis.fromOldWkbType(layer.wkbType()) == QgsWKBTypes.LineStringZ:
                self.__layerList.append(layer)

    def canvasMoveEvent(self, event):
        """
        When the mouse is moved
        :param event: mouse event
        """
        if not self.__isEditing and self.__layerList is not None:
            f_l = Finder.findClosestFeatureLayersAt(event.pos(), self.__layerList, self)

            if f_l is not None and self.__lastFeatureId != f_l[0].id():
                f = f_l[0]
                l = f_l[1]
                self.__lastFeatureId = f.id()
                self.__lastLayer = l
                self.__lastLayer.setSelectedFeatures([f.id()])
            if f_l is not None:
                if self.__counter > 2:
                    self.__rubber.reset()
                    geom = f_l[0].geometry()
                    index = geom.closestVertex(event.mapPoint())[1]
                    line_v2, curved = GeometryV2.asLineV2(geom)
                    num_p = line_v2.numPoints()
                    if num_p > 2 and (index == 0 or index == (num_p-1)):
                        self.__rubber.setIcon(4)
                        self.__rubber.setToGeometry(QgsGeometry(line_v2.pointN(index)), None)
                        self.__counter = 0
                else:
                    self.__counter += 1
            if f_l is None and self.__lastLayer is not None:
                self.__lastLayer.removeSelection()
                self.__rubber.reset()
                self.__lastFeatureId = None

    def canvasReleaseEvent(self, event):
        """
        When the mouse is clicked
        :param event: mouse event
        """
        if self.__lastLayer is not None:
            found_features = self.__lastLayer.selectedFeatures()
            if len(found_features) > 0:
                if len(found_features) < 1:
                    self.__iface.messageBar().pushMessage(
                        QCoreApplication.translate("VDLTools", "One feature at a time"), level=QgsMessageBar.INFO)
                    return
                geom = found_features[0].geometry()
                self.__selectedVertex = geom.closestVertex(event.mapPoint())[1]
                line_v2, curved = GeometryV2.asLineV2(geom)
                num_p = line_v2.numPoints()
                if num_p > 2 and (self.__selectedVertex == 0 or self.__selectedVertex == (num_p-1)):
                    pt = line_v2.pointN(self.__selectedVertex)
                    if self.__selectedVertex == 0:
                        pt0 = line_v2.pointN(2)
                        pt1 = line_v2.pointN(1)
                    else:
                        pt0 = line_v2.pointN(num_p-3)
                        pt1 = line_v2.pointN(num_p-2)
                    big_d = Finder.sqrDistForPoints(pt0, pt1)
                    small_d = Finder.sqrDistForPoints(pt1, pt)
                    if small_d < (big_d/4):
                        self.__isEditing = True
                        self.__selectedFeature = found_features[0]
                        self.__elevation = pt0.z() + (1 + small_d/big_d) * (pt1.z() - pt0.z())
                        if pt.z() is not None and pt.z() != 0:
                            self.__confDlg = ExtrapolateConfirmDialog(pt.z(), self.__elevation)
                            self.__confDlg.okButton().clicked.connect(self.__onEditOk)
                            self.__confDlg.cancelButton().clicked.connect(self.__onEditCancel)
                            self.__confDlg.show()
                        self.__edit()
                    else:
                        self.__iface.messageBar().pushMessage(
                            QCoreApplication.translate("VDLTools", "The segment is too big"), level=QgsMessageBar.INFO)

    def __onEditOk(self):
        """
        When the Ok button in Extrapolate Confirm Dialog is pushed
        """
        self.__confDlg.close()
        self.__edit()

    def __onEditCancel(self):
        """
        When the Cancel button in Extrapolate Confirm Dialog is pushed
        """
        self.__confDlg.close()
        self.__rubber.reset()
        self.__isEditing = False

    def __edit(self):
        """
        To add the new extrapolate elevation
        """
        line_v2, curved = GeometryV2.asLineV2(self.__selectedFeature.geometry())
        line_v2.setZAt(self.__selectedVertex, self.__elevation)
        self.__lastLayer.changeGeometry(self.__selectedFeature.id(), QgsGeometry(line_v2))
        self.__lastLayer.removeSelection()
        self.__rubber.reset()
        self.__lastFeatureId = None
        self.__selectedFeature = None
        self.__selectedVertex = None
        self.__isEditing = False
