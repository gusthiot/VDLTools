# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-10-05
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
from builtins import (range,
                      str)
from math import (sqrt,
                  ceil,
                  floor)
from qgis.core import (QgsPointXY,
                       Qgis)
from qgis.gui import QgsVertexMarker
from qgis.PyQt.QtWidgets import (QDockWidget,
                                 QVBoxLayout,
                                 QFrame,
                                 QHBoxLayout,
                                 QSpinBox,
                                 QLabel,
                                 QComboBox,
                                 QWidget,
                                 QPushButton,
                                 QFileDialog,
                                 QSizePolicy)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import (QSize,
                              QCoreApplication,
                              pyqtSignal)
import traceback
import sys
import json
import requests
from ..core.signal import Signal
from urllib.error import (HTTPError,
                          URLError)

try:
    from matplotlib import pyplot
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
    from matplotlib.backend_bases import MouseButton
    from matplotlib.patches import Rectangle
    matplotlib_loaded = True
except ImportError:
    matplotlib_loaded = False


class ProfileDockWidget(QDockWidget):
    """
    DockWidget class to display the profile
    """

    closeSignal = pyqtSignal()

    def __init__(self, iface, geometry, mntButton=False, zerosButton=False):
        """
        Constructor
        :param iface: interface
        :param geometry: dock widget geometry
        :param mntButton: if button for mnt should be displayed
        :param zerosButton: if button for zeros should be displayed
        """
        QDockWidget.__init__(self)
        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Profile Tool"))
        self.__iface = iface
        self.__geom = geometry
        self.__canvas = self.__iface.mapCanvas()
        self.__types = ['PDF', 'PNG']
        if not matplotlib_loaded:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "No matplotlib lib available"),
                level=Qgis.Critical, duration=0)

        self.__doTracking = False
        self.__vline = None

        self.__profiles = None
        self.__numLines = None
        self.__mntPoints = None

        self.__marker = None
        self.__tabmouseevent = None

        if self.__geom is not None:
            self.setGeometry(self.__geom)

        self.__contentWidget = QWidget()
        self.setWidget(self.__contentWidget)

        self.__boxLayout = QHBoxLayout()
        self.__contentWidget.setLayout(self.__boxLayout)

        self.__plotFrame = QFrame()
        self.__frameLayout = QHBoxLayout()
        self.__plotFrame.setLayout(self.__frameLayout)

        self.__printLayout = QHBoxLayout()
        self.__printLayout.addWidget(self.__plotFrame)

        self.__legendLayout = QVBoxLayout()
        self.__printLayout.addLayout(self.__legendLayout)

        self.__printWdg = QWidget()
        self.__printWdg.setLayout(self.__printLayout)

        self.__rect = None
        self.__clicked_x = None
        self.__clicked_y = None

        self.__plotWdg = None
        self.__scaleButton = None
        self.__activePlotWidget()

        size = QSize(150, 20)

        self.__boxLayout.addWidget(self.__printWdg)

        self.__vertLayout = QVBoxLayout()

        if mntButton:
            self.__displayMnt = False
            self.__mntButton = QPushButton(QCoreApplication.translate("VDLTools", "Display MNT"))
            self.__mntButton.setFixedSize(size)
            self.__mntButton.clicked.connect(self.__mnt)
            self.__vertLayout.addWidget(self.__mntButton)

        if zerosButton:
            self.__displayZeros = False
            self.__zerosButton = QPushButton(QCoreApplication.translate("VDLTools", "Display Zeros"))
            self.__zerosButton.setFixedSize(size)
            self.__zerosButton.clicked.connect(self.__zeros)
            self.__vertLayout.addWidget(self.__zerosButton)
        else:
            self.__displayZeros = True

        self.__scale11 = False
        self.__scaleButton = QPushButton(QCoreApplication.translate("VDLTools", "Scale 1:1"))
        self.__scaleButton.setFixedSize(size)
        self.__scaleButton.clicked.connect(self.__scale)
        self.__vertLayout.addWidget(self.__scaleButton)

        self.__maxLabel = QLabel("y max")
        self.__maxLabel.setFixedSize(size)
        self.__vertLayout.addWidget(self.__maxLabel)
        self.__maxSpin = QSpinBox()
        self.__maxSpin.setFixedSize(size)
        self.__maxSpin.setRange(-10000, 10000)
        self.__maxSpin.valueChanged.connect(self.__reScalePlot)
        self.__vertLayout.addWidget(self.__maxSpin)
        self.__vertLayout.insertSpacing(10, 20)

        self.__minLabel = QLabel("y min")
        self.__minLabel.setFixedSize(size)
        self.__vertLayout.addWidget(self.__minLabel)
        self.__minSpin = QSpinBox()
        self.__minSpin.setFixedSize(size)
        self.__minSpin.setRange(-10000, 10000)
        self.__minSpin.valueChanged.connect(self.__reScalePlot)
        self.__vertLayout.addWidget(self.__minSpin)
        self.__vertLayout.insertSpacing(10, 40)

        self.__typeCombo = QComboBox()
        self.__typeCombo.setFixedSize(size)
        self.__typeCombo.addItems(self.__types)
        self.__vertLayout.addWidget(self.__typeCombo)
        self.__saveButton = QPushButton(QCoreApplication.translate("VDLTools", "Save"))
        self.__saveButton.setFixedSize(size)
        self.__saveButton.clicked.connect(self.__save)
        self.__vertLayout.addWidget(self.__saveButton)

        self.__boxLayout.addLayout(self.__vertLayout)

        self.__maxSpin.setEnabled(False)
        self.__minSpin.setEnabled(False)

        self.__colors = []
        for cn in QColor.colorNames():
            qc = QColor(cn)
            val = qc.red() + qc.green() + qc.blue()
            if 0 < val < 450:
                self.__colors.append(cn)

    def mntButton(self):
        """
        To get the mnt button instance
        :return: mnt button instance
        """
        return self.__mntButton

    def zerosButton(self):
        """
        To get the zeros button instance
        :return: zeros button instance
        """
        return self.__zerosButton

    def scaleButton(self):
        """
        To get the scale button instance
        :return: scale button instance
        """
        return self.__scaleButton

    def displayMnt(self):
        """
        To get if we want to display mnt
        :return: true or false
        """
        return self.__displayMnt

    def __scale(self):
        """
        To toggle between standard and 1:1 scale
        """
        if self.__scale11:
            self.__scale11 = False
            self.__scaleButton.setText(QCoreApplication.translate("VDLTools", "Scale 1:1"))
        else:
            self.__scale11 = True
            self.__scaleButton.setText(QCoreApplication.translate("VDLTools", "Auto scale"))

    def __mnt(self):
        """
        To toggle mnt display choice
        """
        if self.__displayMnt:
            self.__displayMnt = False
            self.__mntButton.setText(QCoreApplication.translate("VDLTools", "Display MNT"))
        else:
            self.__displayMnt = True
            self.__mntButton.setText(QCoreApplication.translate("VDLTools", "Remove MNT"))

    def __zeros(self):
        """
        To toggle if we want to display zero elevations or not
        """
        if self.__displayZeros:
            self.__displayZeros = False
            self.__zerosButton.setText(QCoreApplication.translate("VDLTools", "Display Zeros"))
        else:
            self.__displayZeros = True
            self.__zerosButton.setText(QCoreApplication.translate("VDLTools", "Remove Zeros"))

    def __activePlotWidget(self):
        """
        When plot matplotlib widget is activated
        """
        self.__activateMouseTracking(False)
        while self.__frameLayout.count():
            child = self.__frameLayout.takeAt(0)
            child.widget().deleteLater()
        self.__plotWdg = None

        fig = pyplot.figure()
        pyplot.axis([0, 1000, 0, 1000])

        self.__manageMatplotlibAxe(fig.get_axes()[0])
        self.__plotWdg = FigureCanvasQTAgg(fig)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.__plotWdg.setSizePolicy(sizePolicy)
        self.__frameLayout.addWidget(self.__plotWdg)

    def setProfiles(self, profiles, numLines):
        """
        To set the profiles
        :param profiles: profiles : positions with elevations (for line and points)
        :param numLines: number of selected connected lines
        """
        self.__numLines = numLines
        self.__profiles = profiles
        self.__prepare_points()

    def __getLinearPoints(self):
        """
        To extract the linear points of the profile
        """
        profileLen = 0
        self.__profiles[0]['l'] = profileLen
        for i in range(0, len(self.__profiles)-1):
            x1 = float(self.__profiles[i]['x'])
            y1 = float(self.__profiles[i]['y'])
            x2 = float(self.__profiles[i+1]['x'])
            y2 = float(self.__profiles[i+1]['y'])
            profileLen += sqrt(((x2-x1)*(x2-x1)) + ((y2-y1)*(y2-y1)))
            self.__profiles[i+1]['l'] = profileLen

    def __getMnt(self, settings):
        """
        To get the MN data for the profile
        :param settings: settings containing MN url
        """
        if settings is None or settings.mntUrl is None or settings.mntUrl == "None":
            url = 'https://map.lausanne.ch/prod/wsgi/profile.json'
        elif settings.mntUrl == "":
            return
        else:
            url = settings.mntUrl
        names = ['MNT', 'MNS', 'Rocher (approx.)']
        data = "layers=MNT%2CMNS%2CRocher%20(approx.)&geom=%7B%22type%22%3A%22LineString%22%2C%22coordinates%22%3A%5B"

        pos = 0
        for i in range(len(self.__profiles)):
            if pos > 0:
                data += "%2C"
            pos += 1
            data += "%5B" + str(self.__profiles[i]['x']) + "%2C" + str(self.__profiles[i]['y']) + "%5D"
        data += "%5D%7D&nbPoints=" + str(int(self.__profiles[len(self.__profiles)-1]['l']+1))
        try:
            response = requests.post(url, data=data)
            j = response.text
            j_obj = json.loads(j)
            profile = j_obj['profile']
            self.__mntPoints = []
            self.__mntPoints.append(names)
            mnt_l = []
            mnt_z = []
            for p in range(len(names)):
                z = []
                mnt_z.append(z)
            for pt in profile:
                mnt_l.append(float(pt['dist']))
                values = pt['values']
                for p in range(len(names)):
                    if names[p] in values:
                        mnt_z[p].append(float(values[names[p]]))
                    else:
                        mnt_z[p].append(None)
            self.__mntPoints.append(mnt_l)
            self.__mntPoints.append(mnt_z)
        except HTTPError as er:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "HTTP Error"),
                QCoreApplication.translate("VDLTools", "status error") + "[" + str(er.code) + "] : " + er.reason,
                level=Qgis.Critical, duration=0)
        except URLError as er:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "URL Error"),
                er.reason, level=Qgis.Critical, duration=0)
        except ValueError:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "No MNT values here"),
                level=Qgis.Critical, duration=0)

    def attachCurves(self, names, settings, usedMnts):
        """
        To attach the curves for the layers to the profile
        :param names: layers names
        :param settings: mnt settings
        :param usedMnts: which mnt curves are requested
        """
        if (self.__profiles is None) or (self.__profiles == 0):
            return

        self.__getLinearPoints()
        if usedMnts is not None and (usedMnts[0] or usedMnts[1] or usedMnts[2]):
            self.__getMnt(settings)

        c = 0

        if self.__mntPoints is not None:
            for p in range(len(self.__mntPoints[0])):
                if usedMnts[p]:
                    legend = QLabel("<font color='" + self.__colors[c] + "'>" + self.__mntPoints[0][p]
                                    + "</font>")
                    self.__legendLayout.addWidget(legend)

                    qcol = QColor(self.__colors[c])
                    pyplot.plot(self.__mntPoints[1], self.__mntPoints[2][p],
                                gid=self.__mntPoints[0][p], linewidth=3,
                                color=(qcol.red() / 255.0,
                                       qcol.green() / 255.0,
                                       qcol.blue() / 255.0,
                                       qcol.alpha() / 255.0))
                    c += 1

        if 'z' in self.__profiles[0]:
            for i in range(len(self.__profiles[0]['z'])):
                if i < self.__numLines:
                    v = 0
                else:
                    v = i - self.__numLines + 1
                name = names[v]
                xx = []
                yy = []
                for prof in self.__profiles:
                    if isinstance(prof['z'][i], list):
                        for z in prof['z'][i]:
                            xx.append(prof['l'])
                            yy.append(z)
                    else:
                        xx.append(prof['l'])
                        yy.append(prof['z'][i])

                for j in range(len(yy)):
                    if yy[j] is None:
                        xx[j] = None

                if i == 0 or i > (self.__numLines-1):
                    legend = QLabel("<font color='" + self.__colors[c] + "'>" + name + "</font>")
                    self.__legendLayout.addWidget(legend)

                qcol = QColor(self.__colors[c])
                if i < self.__numLines:
                    pyplot.plot(xx, yy, gid=name, linewidth=3, color=(qcol.red() / 255.0,
                                                                      qcol.green() / 255.0,
                                                                      qcol.blue() / 255.0,
                                                                      qcol.alpha() / 255.0))
                else:
                    pyplot.plot(xx, yy, gid=name, linewidth=5, marker='o',
                                linestyle='None', color=(qcol.red() / 255.0,
                                                         qcol.green() / 255.0,
                                                         qcol.blue() / 255.0,
                                                         qcol.alpha() / 255.0))
                c += 1

        # scaling this
        try:
            self.__reScalePlot(None, True)
        except:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "Rescale problem... (trace printed)"),
                level=Qgis.Critical, duration=0)
            print(sys.exc_info()[0], traceback.format_exc())
        self.__plotWdg.draw()
        self.__activateMouseTracking(True)
        self.__marker.show()

    def __reScalePlot(self, value=None, auto=False):
        """
        To rescale the profile plot depending to the bounds
        :param value: juste because connections give value
        :param auto: if automatic ranges calcul is wanted
        """
        if (self.__profiles is None) or (self.__profiles == 0):
            self.__plotWdg.draw()
            return

        minimumValue = self.__minSpin.value()
        maximumValue = self.__maxSpin.value()

        length = 0
        for i in range(len(self.__profiles)):
            if (ceil(self.__profiles[i]['l'])) > length:
                length = ceil(self.__profiles[i]['l'])

        if auto:
            self.__plotWdg.figure.get_axes()[0].set_xbound(0, length)

            minimumValue = 1000000000
            maximumValue = -1000000000
            for i in range(len(self.__profiles)):
                if 'z' in self.__profiles[i]:
                    mini = self.__minTab(self.__profiles[i]['z'])
                    if (mini > 0 or self.__displayZeros) and mini < minimumValue:
                        minimumValue = ceil(mini) - 1
                    maxi = self.__maxTab(self.__profiles[i]['z'])
                    if maxi > maximumValue:
                        maximumValue = floor(maxi) + 1
                if self.__mntPoints is not None:
                    for pts in self.__mntPoints[2]:
                        miniMnt = self.__minTab(pts)
                        if (miniMnt > 0 or self.__displayZeros) and miniMnt < minimumValue:
                            minimumValue = ceil(miniMnt) - 1
                        maxiMnt = self.__maxTab(pts)
                        if maxiMnt > maximumValue:
                            maximumValue = floor(maxiMnt) + 1

            # to draw vertical lines
            for i in range(len(self.__profiles)):
                zz = []
                for j in range(self.__numLines):
                    if self.__profiles[i]['z'][j] is not None:
                        zz.append(j)
                if len(zz) == 2:
                    width = 3
                else:
                    width = 1

                self.__plotWdg.figure.get_axes()[0].vlines(self.__profiles[i]['l'], minimumValue, maximumValue,
                                                           linewidth=width)
        if self.__scale11:
            width = self.__plotWdg.figure.get_figwidth()
            height = self.__plotWdg.figure.get_figheight()
            density = length/width
            interval = density * height
            print(length, interval)
            middle = (maximumValue + minimumValue) / 2
            maximumValue = middle + (interval/2)
            minimumValue = middle - (interval/2)
            print(middle, minimumValue, maximumValue)

        self.__maxSpin.valueChanged.disconnect(self.__reScalePlot)
        self.__maxSpin.setValue(maximumValue)
        self.__maxSpin.valueChanged.connect(self.__reScalePlot)
        self.__minSpin.valueChanged.disconnect(self.__reScalePlot)
        self.__minSpin.setValue(minimumValue)
        self.__minSpin.valueChanged.connect(self.__reScalePlot)
        self.__maxSpin.setEnabled(True)
        self.__minSpin.setEnabled(True)

        if minimumValue < maximumValue:
            self.__plotWdg.figure.get_axes()[0].set_ybound(minimumValue, maximumValue)
            self.__plotWdg.draw()

    @staticmethod
    def __minTab(tab):
        """
        To get the minimum value in a table
        :param tab: table to scan
        :return: minimum value
        """
        mini = 1000000000
        for t in tab:
            if isinstance(t, list):
                for ti in t:
                    if ti is None:
                        continue
                    if ti < mini:
                        mini = ti
            else:
                if t is None:
                    continue
                if t < mini:
                    mini = t
        return mini

    @staticmethod
    def __maxTab(tab):
        """
        To get the maximum value in a table
        :param tab: table to scan
        :return: maximum value
        """
        maxi = -1000000000
        for t in tab:
            if isinstance(t, list):
                for ti in t:
                    if ti is None:
                        continue
                    if ti > maxi:
                        maxi = ti
            else:
                if t is None:
                    continue
                if t > maxi:
                    maxi = t
        return maxi

    def __save(self):
        """
        To save the profile in a file, on selected format
        """
        idx = self.__typeCombo.currentIndex()
        if idx == 0:
            self.__outPDF()
        elif idx == 1:
            self.__outPNG()
        else:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "Invalid index ") + str(idx),
                level=Qgis.Critical, duration=0)

    def __outPDF(self):
        """
        To save the profile as pdf file
        """
        fileName = QFileDialog.getSaveFileName(
            self.__iface.mainWindow(), QCoreApplication.translate("VDLTools", "Save As"),
            QCoreApplication.translate("VDLTools", "Profile.pdf"), "Portable Document Format (*.pdf)")[0]
        if fileName is not None:
            self.__plotWdg.figure.savefig(str(fileName))

    def __outPNG(self):
        """
        To save the profile as png file
        """
        fileName = QFileDialog.getSaveFileName(
            self.__iface.mainWindow(), QCoreApplication.translate("VDLTools", "Save As"),
            QCoreApplication.translate("VDLTools", "Profile.png"), "Portable Network Graphics (*.png)")[0]
        if fileName is not None:
            self.__printWdg.grab().save(fileName, "PNG")

    def clearData(self):
        """
        To clear the displayed data
        """
        if self.__profiles is None:
            return
        self.__plotWdg.figure.get_axes()[0].cla()
        self.__manageMatplotlibAxe(self.__plotWdg.figure.get_axes()[0])
        self.__maxSpin.setEnabled(False)
        self.__minSpin.setEnabled(False)
        self.__maxSpin.valueChanged.disconnect(self.__reScalePlot)
        self.__maxSpin.setValue(0)
        self.__maxSpin.valueChanged.connect(self.__reScalePlot)
        self.__minSpin.valueChanged.disconnect(self.__reScalePlot)
        self.__minSpin.setValue(0)
        self.__minSpin.valueChanged.connect(self.__reScalePlot)

        # clear legend
        while self.__legendLayout.count():
            child = self.__legendLayout.takeAt(0)
            child.widget().deleteLater()

    def __manageMatplotlibAxe(self, axe):
        """
        To manage the axes for matplotlib library
        :param axe: the axes element
        """
        axe.grid()
        axe.tick_params(axis="both", which="major", direction="out", length=10, width=1, bottom=True, top=False,
                        left=True, right=False)
        axe.minorticks_on()
        axe.tick_params(axis="both", which="minor", direction="out", length=5, width=1, bottom=True, top=False,
                        left=True, right=False)
        axe.set_xlabel(QCoreApplication.translate("VDLTools", "Distance [m]"))
        axe.set_ylabel(QCoreApplication.translate("VDLTools", "Elevation [m]"))
        axe.set_position([0.1, 0.2, 0.85, 0.7])

    def __activateMouseTracking(self, activate):
        """
        To (de)activate the mouse tracking on the profile for matplotlib library
        :param activate: true to activate, false to deactivate
        """
        if activate:
            self.__doTracking = True
            self.__loadRubber()
            self.__motion = self.__plotWdg.mpl_connect('motion_notify_event', self.__mouse_motion_mpl)
            self.__pressed = self.__plotWdg.mpl_connect('button_press_event', self.__mouse_pressed_mpl)
            self.__released = self.__plotWdg.mpl_connect('button_release_event', self.__mouse_released_mpl)
        elif self.__doTracking:
            self.__doTracking = False
            self.__plotWdg.mpl_disconnect(self.__motion)
            self.__plotWdg.mpl_disconnect(self.__pressed)
            self.__plotWdg.mpl_disconnect(self.__released)
            if self.__marker is not None:
                self.__canvas.scene().removeItem(self.__marker)
            try:
                if self.__vline is not None:
                    self.__plotWdg.figure.get_axes()[0].lines.remove(self.__vline)
                    self.__plotWdg.draw()
            except Exception as e:
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools", "Tracking exception : ") + str(e),
                    level=Qgis.Critical, duration=0)

    def __mouse_pressed_mpl(self, event):
        """
        To manage matplotlib mouse pressed event
        :param event: mouse pressed event
        """
        if event.xdata is not None and event.ydata is not None:
            if event.button == MouseButton.LEFT:
                if self.__rect is None:
                    try:
                        if self.__vline is not None:
                            self.__plotWdg.figure.get_axes()[0].lines.remove(self.__vline)
                            self.__plotWdg.draw()
                    except Exception as e:
                        print(QCoreApplication.translate("VDLTools", "Mouse event exception : ") + str(e))
                        
                    self.__clicked_x = event.xdata
                    self.__clicked_y = event.ydata
                    self.__rect = Rectangle((event.xdata, event.ydata), 0, 0, linewidth=1,
                                            edgecolor='r', facecolor='none')
                    self.__plotWdg.figure.get_axes()[0].add_patch(self.__rect)

    def __mouse_released_mpl(self, event):
        """
        To manage matplotlib mouse released event
        :param event: mouse released event
        """
        if event.button == MouseButton.LEFT:
            self.__plotWdg.figure.get_axes()[0].set_xbound(self.__rect.get_x(),
                                                           (self.__rect.get_x() + self.__rect.get_width()))
            if self.__scale11:
                length = self.__rect.get_width()
                width = self.__plotWdg.figure.get_figwidth()
                height = self.__plotWdg.figure.get_figheight()
                density = length / width
                interval = density * height
                middle = self.__rect.get_y() + self.__rect.get_height()/2
                maximumValue = middle + (interval / 2)
                minimumValue = middle - (interval / 2)
                self.__plotWdg.figure.get_axes()[0].set_ybound(minimumValue, maximumValue)
            else:
                self.__plotWdg.figure.get_axes()[0].set_ybound(self.__rect.get_y(),
                                                               (self.__rect.get_y()+self.__rect.get_height()))
            self.__maxSpin.valueChanged.disconnect(self.__reScalePlot)
            self.__maxSpin.setValue(self.__rect.get_y() + self.__rect.get_height())
            self.__maxSpin.valueChanged.connect(self.__reScalePlot)
            self.__minSpin.valueChanged.disconnect(self.__reScalePlot)
            self.__minSpin.setValue(self.__rect.get_y())
            self.__minSpin.valueChanged.connect(self.__reScalePlot)

            self.__plotWdg.figure.get_axes()[0].patches = []
            self.__plotWdg.draw()
            self.__clicked_x = None
            self.__clicked_y = None
            self.__rect = None
        elif event.button == MouseButton.RIGHT:
            self.__reScalePlot(None, True)

    def __mouse_motion_mpl(self, event):
        """
        To manage matplotlib mouse motion event
        :param event: mouse motion event
        """
        if self.__rect is not None:
            if event.xdata is not None and event.ydata is not None:
                if event.xdata < self.__clicked_x:
                    self.__rect.set_x(event.xdata)
                    self.__rect.set_width(self.__clicked_x-event.xdata)
                else:
                    self.__rect.set_width(event.xdata-self.__clicked_x)
                if event.ydata < self.__clicked_y:
                    self.__rect.set_y(event.ydata)
                    self.__rect.set_height(self.__clicked_y-event.ydata)
                else:
                    self.__rect.set_height(event.ydata-self.__clicked_y)
                self.__plotWdg.draw()

        elif event.xdata is not None:
            try:
                if self.__vline is not None:
                    self.__plotWdg.figure.get_axes()[0].lines.remove(self.__vline)
            except Exception as e:
                print(QCoreApplication.translate("VDLTools", "Mouse event exception : ") + str(e))
            xdata = float(event.xdata)
            self.__vline = self.__plotWdg.figure.get_axes()[0].axvline(xdata, linewidth=2, color='k')
            self.__plotWdg.draw()
            i = 1
            while i < len(self.__tabmouseevent)-1 and xdata > self.__tabmouseevent[i][0]:
                i += 1
            i -= 1

            x = self.__tabmouseevent[i][1] + (self.__tabmouseevent[i + 1][1] - self.__tabmouseevent[i][1]) / (
                    self.__tabmouseevent[i + 1][0] - self.__tabmouseevent[i][0]) * (xdata - self.__tabmouseevent[i][0])
            y = self.__tabmouseevent[i][2] + (self.__tabmouseevent[i + 1][2] - self.__tabmouseevent[i][2]) / (
                    self.__tabmouseevent[i + 1][0] - self.__tabmouseevent[i][0]) * (xdata - self.__tabmouseevent[i][0])
            self.__marker.show()
            self.__marker.setCenter(QgsPointXY(x, y))

    def __loadRubber(self):
        """
        To load te rubber band for mouse tracking on map
        """
        self.__marker = QgsVertexMarker(self.__canvas)
        self.__marker.setIconSize(5)
        self.__marker.setIconType(QgsVertexMarker.ICON_BOX)
        self.__marker.setPenWidth(3)

    def __prepare_points(self):
        """
        To prepare the points on map for mouse tracking on profile
        """
        self.__tabmouseevent = []
        length = 0
        for i, point in enumerate(self.__profiles):
            if i == 0:
                self.__tabmouseevent.append([0, point['x'], point['y']])
            else:
                length += ((self.__profiles[i]['x'] - self.__profiles[i-1]['x']) ** 2 +
                           (self.__profiles[i]['y'] - self.__profiles[i-1]['y']) ** 2) ** 0.5
                self.__tabmouseevent.append([float(length), float(point['x']), float(point['y'])])

    def closeEvent(self, event):
        """
        When the dock widget is closed
        :param event: close event
        """
        if self.__maxSpin is not None:
            Signal.safelyDisconnect(self.__maxSpin.valueChanged, self.__reScalePlot)
            self.__maxSpin = None
        if self.__minSpin is not None:
            Signal.safelyDisconnect(self.__minSpin.valueChanged, self.__reScalePlot)
            self.__minSpin = None
        if self.__saveButton is not None:
            Signal.safelyDisconnect(self.__saveButton.clicked, self.__save)
            self.__saveButton = None
        self.closeSignal.emit()
        if self.__marker is not None:
            self.__marker.hide()
        QDockWidget.closeEvent(self, event)
