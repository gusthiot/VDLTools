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

from qgis.core import QgsPoint, QgsGeometry, QgsFeature
from datetime import datetime
from math import cos, sin, pi


class Orientation:
    def __init__(self, point, observation, precision, lineLayer, pointLayer, length):
        self.lineLayer = lineLayer
        self.pointLayer = pointLayer
        self.length = length

        self.id = datetime.now().strftime("%Y%m%d%H%M%S%f")

        self.point = QgsPoint(point)
        self.observation = observation
        self.precision = precision

    def save(self):
        # observation
        f = QgsFeature()
        fields = self.lineLayer.dataProvider().fields()
        f.setFields(fields)
        f["id"] = self.id
        f["x"] = self.point.x()
        f["y"] = self.point.y()
        f["observation"] = self.observation
        f["precision"] = self.precision
        f.setGeometry(self.geometry())
        ok, l = self.lineLayer.dataProvider().addFeatures([f])
        self.lineLayer.updateExtents()
        self.lineLayer.setCacheImage(None)
        self.lineLayer.triggerRepaint()
        self.lineLayer.featureAdded.emit(l[0].id())  # emit signal so feature is added to snapping index

        # center
        f = QgsFeature()
        fields = self.pointLayer.dataProvider().fields()
        f.setFields(fields)
        f["id"] = self.id
        f.setGeometry(QgsGeometry().fromPoint(self.point))
        ok, l = self.pointLayer.dataProvider().addFeatures([f])
        self.pointLayer.updateExtents()
        self.pointLayer.setCacheImage(None)
        self.pointLayer.triggerRepaint()
        self.pointLayer.featureAdded.emit(l[0].id())  # emit signal so feature is added to snapping index

    def geometry(self):
        x = self.point.x() + self.length * cos((90-self.observation)*pi/180)
        y = self.point.y() + self.length * sin((90-self.observation)*pi/180)
        return QgsGeometry().fromPolyline([self.point, QgsPoint(x, y)])
