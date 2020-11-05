# -----------------------------------------------------------
#
# Intersect It is a QGIS plugin to place observations (distance or orientation)
# with their corresponding precision, intersect them using a least-squares solution
# and save dimensions in a dedicated layer to produce maps.
#
# Copyright    : (C) 2013 Denis Rouzaud
# Email        : denis.rouzaud@gmail.com
#
# -----------------------------------------------------------
#
# licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# ---------------------------------------------------------------------
"""
Reimplemented for QGIS3 by :

/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2020-08-08
        git sha              : $Format:%H$
        copyright            : (C) 2020 Ville de Lausanne
        author               : Christophe Gusthiot
        email                : i2g@gusthiot.ch
 ***************************************************************************/
"""

from qgis.core import (QgsPoint,
                       Qgis,
                       QgsGeometry,
                       QgsFeature)
from datetime import datetime
from math import (cos,
                  sin,
                  pi)
from qgis.PyQt.QtCore import QCoreApplication


class Orientation:
    """
    Class representing orientation
    """

    def __init__(self, iface, point, azimut):
        """
        Constructor
        :param point: base point
        :param azimut: mesured azimut
        """
        self.iface = iface
        self.point = point
        self.azimut = azimut
        self.length = 8.0
        # self.precision = 0.5

    def save(self, lineLayer, pointLayer):
        """
        To save the orientation
        """
        did = datetime.now().strftime("%Y%m%d%H%M%S%f")

        # observation
        f = QgsFeature()
        fields = lineLayer.dataProvider().fields()
        f.setFields(fields)
        fieldsNames = [fields.at(pos).name() for pos in range(fields.count())]
        if "id" in fieldsNames:
            f.setAttribute("id", did)
        else:
            self.iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "no 'id' attribute in line layer"),
                level=Qgis.Warning)
        if "type" in fieldsNames:
            f.setAttribute("type", "orientation")
        else:
            self.iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "no 'type' attribute in line layer"),
                level=Qgis.Warning)
        if "mesure" in fieldsNames:
            f.setAttribute("mesure", self.azimut)
        else:
            self.iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "no 'mesure' attribute in line layer"),
                level=Qgis.Warning)
        if "x" in fieldsNames:
            f.setAttribute("x", self.point.x())
        else:
            self.iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "no 'x' attribute in line layer"),
                level=Qgis.Warning)
        if "y" in fieldsNames:
            f.setAttribute("y", self.point.y())
        else:
            self.iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "no 'y' attribute in line layer"),
                level=Qgis.Warning)
        f.setGeometry(self.geometry())
        ok, l = lineLayer.dataProvider().addFeatures([f])
        lineLayer.updateExtents()
        lineLayer.triggerRepaint()
        lineLayer.featureAdded.emit(l[0].id())  # emit signal so feature is added to snapping index

        # center
        f = QgsFeature()
        fields = pointLayer.dataProvider().fields()
        f.setFields(fields)
        fieldsNames = [fields.at(pos).name() for pos in range(fields.count())]
        if "id" in fieldsNames:
            f.setAttribute("id", did)
        else:
            self.iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "no 'id' attribute in point layer"),
                level=Qgis.Warning)
        f.setGeometry(QgsGeometry().fromPointXY(self.point))
        ok, l = pointLayer.dataProvider().addFeatures([f])
        pointLayer.updateExtents()
        pointLayer.triggerRepaint()
        pointLayer.featureAdded.emit(l[0].id())  # emit signal so feature is added to snapping index

    def geometry(self):
        """
        To generate the orientation geometry
        """
        x = self.point.x() + self.length * cos((90-self.azimut)*pi/180)
        y = self.point.y() + self.length * sin((90-self.azimut)*pi/180)
        return QgsGeometry().fromPolyline([QgsPoint(self.point), QgsPoint(x, y)])