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
from __future__ import print_function
from __future__ import division
from future import standard_library
from future.builtins import str
from future.builtins import range
from math import sqrt
from matplotlib import rc
from past.utils import old_div
from qgis.core import QgsPoint
from qgis.gui import (QgsVertexMarker,
                      QgsMessageBar)
from PyQt4.QtGui import (QDockWidget,
                         QVBoxLayout,
                         QFrame,
                         QHBoxLayout,
                         QSpinBox,
                         QLabel,
                         QComboBox,
                         QWidget,
                         QPushButton,
                         QPen,
                         QColor,
                         QFont,
                         QPixmap,
                         QFileDialog,
                         QSizePolicy,
                         QPrinter)
from PyQt4.QtCore import (QSize,
                          QRectF,
                          QCoreApplication,
                          Qt,
                          pyqtSignal)
import itertools
import traceback
import sys
import json
from ..core.signal import Signal
from future.moves.urllib.request import urlopen
from future.moves.urllib.error import (HTTPError,
                                       URLError)

try:
    from PyQt4.Qwt5.Qwt import (QwtPlot,
                                QwtText,
                                QwtPlotZoomer,
                                QwtPicker,
                                QwtPlotItem,
                                QwtPlotGrid,
                                QwtPlotMarker,
                                QwtPlotCurve)
    Qwt5_loaded = True
except ImportError:
    Qwt5_loaded = False
try:
    from matplotlib.figure import Figure, SubplotParams
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
    matplotlib_loaded = True
except ImportError:
    matplotlib_loaded = False

standard_library.install_aliases()


class ProfileDockWidget(QDockWidget):
    """
    DockWidget class to display the profile
    """

    closeSignal = pyqtSignal()

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        QDockWidget.__init__(self)
        self.setWindowTitle(QCoreApplication.translate("VDLTools", "Profile Tool"))
        self.resize(1024, 400)
        self.__iface = iface
        self.__canvas = self.__iface.mapCanvas()
        self.__types = ['PDF', 'PNG']  # ], 'SVG', 'PS']
        self.__libs = []
        if Qwt5_loaded:
            self.__lib = 'Qwt5'
            self.__libs.append('Qwt5')
            if matplotlib_loaded:
                self.__libs.append('Matplotlib')
        elif matplotlib_loaded:
            self.__lib = 'Matplotlib'
            self.__libs.append('Matplotlib')
        else:
            self.__lib = None
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "No graph lib available (qwt5 or matplotlib)"),
                level=QgsMessageBar.CRITICAL, duration=0)

        self.__doTracking = False
        self.__vline = None

        self.__profiles = None
        self.__numLines = None
        self.__mntPoints = None

        self.__marker = None
        self.__tabmouseevent = None

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

        self.__plotWdg = None
        self.__changePlotWidget()

        size = QSize(150, 20)

        self.__boxLayout.addWidget(self.__printWdg)

        self.__vertLayout = QVBoxLayout()

        self.__libCombo = QComboBox()
        self.__libCombo.setFixedSize(size)
        self.__libCombo.addItems(self.__libs)
        self.__vertLayout.addWidget(self.__libCombo)
        self.__libCombo.currentIndexChanged.connect(self.__setLib)

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

    def __changePlotWidget(self):
        """
        When plot widget is change (qwt <-> matplotlib)
        """
        self.__activateMouseTracking(False)
        while self.__frameLayout.count():
            child = self.__frameLayout.takeAt(0)
            child.widget().deleteLater()
        self.__plotWdg = None

        if self.__lib == 'Qwt5':
            self.__plotWdg = QwtPlot(self.__plotFrame)
            sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            sizePolicy.setHorizontalStretch(10)
            sizePolicy.setVerticalStretch(0)
            self.__plotWdg.setSizePolicy(sizePolicy)
            self.__plotWdg.setAutoFillBackground(False)
            # Decoration
            self.__plotWdg.setCanvasBackground(Qt.white)
            self.__plotWdg.plotLayout().setAlignCanvasToScales(False)
            self.__plotWdg.plotLayout().setSpacing(100)
            self.__plotWdg.plotLayout().setCanvasMargin(10, QwtPlot.xBottom)
            self.__plotWdg.plotLayout().setCanvasMargin(10, QwtPlot.yLeft)
            title = QwtText(QCoreApplication.translate("VDLTools", "Distance [m]"))
            title.setFont(QFont("Helvetica", 10))
            self.__plotWdg.setAxisTitle(QwtPlot.xBottom, title)
            title.setText(QCoreApplication.translate("VDLTools", "Elevation [m]"))
            title.setFont(QFont("Helvetica", 10))
            self.__plotWdg.setAxisTitle(QwtPlot.yLeft, title)
            self.__zoomer = QwtPlotZoomer(QwtPlot.xBottom, QwtPlot.yLeft, QwtPicker.DragSelection, QwtPicker.AlwaysOff,
                                          self.__plotWdg.canvas())
            self.__zoomer.setRubberBandPen(QPen(Qt.blue))
            grid = QwtPlotGrid()
            grid.setPen(QPen(QColor('grey'), 0, Qt.DotLine))
            grid.attach(self.__plotWdg)
            self.__frameLayout.addWidget(self.__plotWdg)

        elif self.__lib == 'Matplotlib':
            # __plotWdg.figure : matplotlib.figure.Figure
            fig = Figure((1.0, 1.0), linewidth=0.0, subplotpars=SubplotParams(left=0, bottom=0, right=1, top=1,
                                                                              wspace=0, hspace=0))

            font = {'family': 'arial', 'weight': 'normal', 'size': 12}
            rc('font', **font)

            rect = fig.patch
            rect.set_facecolor((0.9, 0.9, 0.9))

            self.__axes = fig.add_axes((0.07, 0.16, 0.92, 0.82))
            self.__axes.set_xbound(0, 1000)
            self.__axes.set_ybound(0, 1000)
            self.__manageMatplotlibAxe(self.__axes)
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
        if self.__lib == 'Matplotlib':
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
        if settings is None or settings.mntUrl() is None or settings.mntUrl() == "None":
            url = 'http://map.lausanne.ch/main/wsgi/profile.json'
        elif settings.mntUrl() == "":
            return
        else:
            url = settings.mntUrl()
        names = ['mnt', 'mns', 'toit_rocher']
        url += '?layers='
        pos = 0
        for name in names:
            if pos > 0:
                url += ','
            pos += 1
            url += name
        url += '&geom={"type":"LineString", "coordinates":['
        pos = 0
        for i in range(len(self.__profiles)):
            if pos > 0:
                url += ','
            pos += 1
            url += '[' + str(self.__profiles[i]['x']) + ',' + str(self.__profiles[i]['y']) + ']'
        url = url + ']}&nbPoints=' + str(int(self.__profiles[len(self.__profiles)-1]['l']))
        try:
            response = urlopen(url)
            j = response.read()
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
                    mnt_z[p].append(float(values[names[p]]))
            self.__mntPoints.append(mnt_l)
            self.__mntPoints.append(mnt_z)
        except HTTPError as e:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "HTTP Error"),
                QCoreApplication.translate("VDLTools", "status error [" + str(e.code) + "] : " + e.reason),
                level=QgsMessageBar.CRITICAL, duration=0)
        except URLError as e:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "URL Error"),
                e.reason, level=QgsMessageBar.CRITICAL, duration=0)

    def attachCurves(self, names, settings, usedMnts):
        """
        To attach the curves for the layers to the profile
        :param names: layers names
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

                        if self.__lib == 'Qwt5':

                            xx = [list(g) for k, g in itertools.groupby(self.__mntPoints[1],
                                                                        lambda x: x is None) if not k]
                            yy = [list(g) for k, g in itertools.groupby(self.__mntPoints[2][p], lambda x: x is None)
                                  if not k]

                            for j in range(len(xx)):
                                curve = QwtPlotCurve(self.__mntPoints[0][p])
                                curve.setData(xx[j], yy[j])
                                curve.setPen(QPen(QColor(self.__colors[c]), 3))
                                curve.attach(self.__plotWdg)

                        elif self.__lib == 'Matplotlib':
                            qcol = QColor(self.__colors[c])
                            self.__plotWdg.figure.get_axes()[0].plot(self.__mntPoints[1], self.__mntPoints[2][p],
                                                                     gid=self.__mntPoints[0][p], linewidth=3)
                            tmp = self.__plotWdg.figure.get_axes()[0].get_lines()
                            for t in range(len(tmp)):
                                if self.__mntPoints[0][p] == tmp[t].get_gid():
                                    tmp[c].set_color((old_div(qcol.red(), 255.0), old_div(qcol.green(), 255.0),
                                                      old_div(qcol.blue(), 255.0), old_div(qcol.alpha(), 255.0)))
                                    self.__plotWdg.draw()
                                    break
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
                    xx.append(prof['l'])
                    yy.append(prof['z'][i])

                for j in range(len(yy)):
                    if yy[j] is None:
                        xx[j] = None

                if i == 0 or i > (self.__numLines-1):
                    legend = QLabel("<font color='" + self.__colors[c] + "'>" + name + "</font>")
                    self.__legendLayout.addWidget(legend)

                if self.__lib == 'Qwt5':

                    # Split xx and yy into single lines at None values
                    xx = [list(g) for k, g in itertools.groupby(xx, lambda x: x is None) if not k]
                    yy = [list(g) for k, g in itertools.groupby(yy, lambda x: x is None) if not k]

                    # Create & attach one QwtPlotCurve per one single line
                    for j in range(len(xx)):
                        curve = QwtPlotCurve(name)
                        curve.setData(xx[j], yy[j])
                        curve.setPen(QPen(QColor(self.__colors[c]), 3))
                        if i > (self.__numLines-1):
                            curve.setStyle(QwtPlotCurve.Dots)
                            pen = QPen(QColor(self.__colors[c]), 8)
                            pen.setCapStyle(Qt.RoundCap)
                            curve.setPen(pen)
                        curve.attach(self.__plotWdg)

                elif self.__lib == 'Matplotlib':
                    qcol = QColor(self.__colors[c])
                    if i < self.__numLines:
                        self.__plotWdg.figure.get_axes()[0].plot(xx, yy, gid=name, linewidth=3)
                    else:
                        self.__plotWdg.figure.get_axes()[0].plot(xx, yy, gid=name, linewidth=5, marker='o',
                                                                 linestyle='None')
                    tmp = self.__plotWdg.figure.get_axes()[0].get_lines()
                    for t in range(len(tmp)):
                        if name == tmp[t].get_gid():
                            tmp[c].set_color((old_div(qcol.red(), 255.0), old_div(qcol.green(), 255.0),
                                              old_div(qcol.blue(), 255.0), old_div(qcol.alpha(), 255.0)))
                            self.__plotWdg.draw()
                            break
                c += 1

        # scaling this
        try:
            self.__reScalePlot(None, True)
        except:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools", "Rescale problem... (trace printed)"),
                level=QgsMessageBar.CRITICAL, duration=0)
            print(
                QCoreApplication.translate("VDLTools", "rescale problem : "), sys.exc_info()[0], traceback.format_exc())
        if self.__lib == 'Qwt5':
            self.__plotWdg.replot()
        elif self.__lib == 'Matplotlib':
            self.__plotWdg.figure.get_axes()[0].redraw_in_frame()
            self.__plotWdg.draw()
            self.__activateMouseTracking(True)
            self.__marker.show()

    def __reScalePlot(self, value=None, auto=False):
        """
        To rescale the profile plot depending to the bounds
        """
        if (self.__profiles is None) or (self.__profiles == 0):
            self.__plotWdg.replot()
            return

        maxi = 0
        for i in range(len(self.__profiles)):
            if (int(self.__profiles[i]['l'])) > maxi:
                maxi = int(self.__profiles[i]['l']) + 1
        if self.__lib == 'Qwt5':
            self.__plotWdg.setAxisScale(2, 0, maxi, 0)
        elif self.__lib == 'Matplotlib':
            self.__plotWdg.figure.get_axes()[0].set_xbound(0, maxi)

        minimumValue = self.__minSpin.value()
        maximumValue = self.__maxSpin.value()

        # to set max y and min y displayed
        if auto:
            minimumValue = 1000000000
            maximumValue = -1000000000
            for i in range(len(self.__profiles)):
                if 'z' in self.__profiles[i]:
                    mini = self.__minTab(self.__profiles[i]['z'])
                    if int(mini) < minimumValue:
                        minimumValue = int(mini) - 1
                    maxi = self.__maxTab(self.__profiles[i]['z'])
                    if int(maxi) > maximumValue:
                        maximumValue = int(maxi) + 1
                if self.__mntPoints is not None:
                    for pts in self.__mntPoints[2]:
                        miniMnt = self.__minTab(pts)
                        if int(miniMnt) < minimumValue:
                            minimumValue = int(miniMnt) - 1
                        maxiMnt = self.__maxTab(pts)
                        if int(maxiMnt) > maximumValue:
                            maximumValue = int(maxiMnt) + 1
        self.__maxSpin.setValue(maximumValue)
        self.__minSpin.setValue(minimumValue)
        self.__maxSpin.setEnabled(True)
        self.__minSpin.setEnabled(True)

        if self.__lib == 'Qwt5':
            rect = QRectF(0, minimumValue, maxi, maximumValue-minimumValue)
            self.__zoomer.setZoomBase(rect)

        # to draw vertical lines
        for i in range(len(self.__profiles)):
            zz = []
            for j in range(self.__numLines):
                if self.__profiles[i]['z'][j] is not None:
                    zz.append(j)
            color = None
            if len(zz) == 2:
                width = 3
                color = QColor('red')
            else:
                width = 1

            if self.__lib == 'Qwt5':
                vertLine = QwtPlotMarker()
                vertLine.setLineStyle(QwtPlotMarker.VLine)
                pen = vertLine.linePen()
                pen.setWidth(width)
                if color is not None:
                    pen.setColor(color)
                vertLine.setLinePen(pen)
                vertLine.setXValue(self.__profiles[i]['l'])
                label = vertLine.label()
                label.setText(str(i))
                vertLine.setLabel(label)
                vertLine.setLabelAlignment(Qt.AlignLeft)
                vertLine.attach(self.__plotWdg)
            elif self.__lib == 'Matplotlib':
                self.__plotWdg.figure.get_axes()[0].vlines(self.__profiles[i]['l'], minimumValue, maximumValue,
                                                           linewidth=width)

        if minimumValue < maximumValue:
            if self.__lib == 'Qwt5':
                self.__plotWdg.setAxisScale(0, minimumValue, maximumValue, 0)
                self.__plotWdg.replot()
            elif self.__lib == 'Matplotlib':
                self.__plotWdg.figure.get_axes()[0].set_ybound(minimumValue, maximumValue)
                self.__plotWdg.figure.get_axes()[0].redraw_in_frame()
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
            if t is None:
                continue
            if t > maxi:
                maxi = t
        return maxi

    def __setLib(self):
        """
        To set the new widget library (qwt <-> matplotlib)
        """
        self.__lib = self.__libs[self.__libCombo.currentIndex()]
        self.__changePlotWidget()

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
                level=QgsMessageBar.CRITICAL, duration=0)

    def __outPDF(self):
        """
        To save the profile as pdf file
        """
        fileName = QFileDialog.getSaveFileName(
            self.__iface.mainWindow(), QCoreApplication.translate("VDLTools", "Save As"),
            QCoreApplication.translate("VDLTools", "Profile.pdf"),"Portable Document Format (*.pdf)")
        if fileName is not None:
            if self.__lib == 'Qwt5':
                printer = QPrinter()
                printer.setCreator(QCoreApplication.translate("VDLTools", "QGIS Profile Plugin"))
                printer.setOutputFileName(fileName)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOrientation(QPrinter.Landscape)
                self.__plotWdg.print_(printer)
            elif self.__lib == 'Matplotlib':
                self.__plotWdg.figure.savefig(str(fileName))
            # printer = QPrinter()
            # printer.setCreator(QCoreApplication.translate("VDLTools", "QGIS Profile Plugin"))
            # printer.setOutputFileName(fileName)
            # printer.setOutputFormat(QPrinter.PdfFormat)
            # printer.setOrientation(QPrinter.Landscape)
            # printer.setPaperSize(QSizeF(self.__printWdg.size()), QPrinter.Millimeter)
            # printer.setFullPage(True)
            # self.__printWdg.render(printer)

    def __outPNG(self):
        """
        To save the profile as png file
        """
        fileName = QFileDialog.getSaveFileName(
            self.__iface.mainWindow(), QCoreApplication.translate("VDLTools", "Save As"),
            QCoreApplication.translate("VDLTools", "Profile.png"),"Portable Network Graphics (*.png)")
        if fileName is not None:
            QPixmap.grabWidget(self.__printWdg).save(fileName, "PNG")

    def clearData(self):
        """
        To clear the displayed data
        """
        if self.__profiles is None:
            return
        if self.__lib == 'Qwt5':
            self.__plotWdg.clear()
            self.__profiles = None
            temp1 = self.__plotWdg.itemList()
            for j in range(len(temp1)):
                if temp1[j].rtti() == QwtPlotItem.Rtti_PlotCurve:
                    temp1[j].detach()
        elif self.__lib == 'Matplotlib':
            self.__plotWdg.figure.get_axes()[0].cla()
            self.__manageMatplotlibAxe(self.__plotWdg.figure.get_axes()[0])
        self.__maxSpin.setEnabled(False)
        self.__minSpin.setEnabled(False)
        self.__maxSpin.setValue(0)
        self.__minSpin.setValue(0)

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

    def __activateMouseTracking(self, activate):
        """
        To (de)activate the mouse tracking on the profile for matplotlib library
        :param activate: true to activate, false to deactivate
        """
        if activate:
            self.__doTracking = True
            self.__loadRubber()
            self.cid = self.__plotWdg.mpl_connect('motion_notify_event', self.__mouseevent_mpl)
        elif self.__doTracking:
            self.__doTracking = False
            self.__plotWdg.mpl_disconnect(self.cid)
            if self.__marker is not None:
                self.__canvas.scene().removeItem(self.__marker)
            try:
                if self.__vline is not None:
                    self.__plotWdg.figure.get_axes()[0].lines.remove(self.__vline)
                    self.__plotWdg.draw()
            except Exception as e:
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools", "Tracking exception : ") + str(e),
                    level=QgsMessageBar.CRITICAL, duration=0)

    def __mouseevent_mpl(self, event):
        """
        To manage matplotlib mouse tracking event
        :param event: mouse tracking event
        """
        if event.xdata is not None:
            try:
                if self.__vline is not None:
                    self.__plotWdg.figure.get_axes()[0].lines.remove(self.__vline)
            except Exception as e:
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools", "Mouse event exception : ") + str(e),
                    level=QgsMessageBar.CRITICAL, duration=0)
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
            self.__marker.setCenter(QgsPoint(x, y))

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
        if self.__libCombo is not None:
            Signal.safelyDisconnect(self.__libCombo.currentIndexChanged, self.__setLib)
            self.__libCombo = None
        self.closeSignal.emit()
        if self.__marker is not None:
            self.__marker.hide()
        QDockWidget.closeEvent(self, event)
