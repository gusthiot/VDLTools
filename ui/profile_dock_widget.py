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
                         QPrintDialog,
                         QSizePolicy,
                         QPrinter)
from PyQt4.QtCore import (QSize,
                          QRectF,
                          QCoreApplication,
                          Qt)
from PyQt4.QtSvg import QSvgGenerator
from PyQt4.Qwt5 import (QwtPlot,
                        QwtText,
                        QwtPlotZoomer,
                        QwtPicker,
                        QwtPlotItem,
                        Qwt,
                        QwtPlotMarker,
                        QwtSymbol,
                        QwtPlotCurve)
import itertools
import traceback
import sys
from math import sqrt
from matplotlib import rc
from matplotlib.figure import Figure, SubplotParams
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg  # , NavigationToolbar2QTAgg


class ProfileDockWidget(QDockWidget):
    def __init__(self, iface):
        QDockWidget.__init__(self)
        self.setWindowTitle(QCoreApplication.translate("VDLTools","Profile Tool"))
        self.resize(1024, 400)
        self.__iface = iface
        self.__canvas = self.__iface.mapCanvas()
        self.__types = ['PDF', 'PNG', 'SVG', 'PS']
        self.__libs = ['Matplotlib', 'Qwt5']
        self.__lib = self.__libs[0]
        self.__doTracking = False
        self.__vline = None

        self.__profiles = None
        self.__numLines = None

        self.__rubberband = None
        self.__tabmouseevent = None

        self.__contentWidget = QWidget()
        self.setWidget(self.__contentWidget)

        self.__boxLayout = QHBoxLayout()
        self.__contentWidget.setLayout(self.__boxLayout)

        self.__plotFrame = QFrame()
        self.__frameLayout = QHBoxLayout()
        self.__plotFrame.setLayout(self.__frameLayout)

        self.__plotWdg = None
        self.__changePlotWidget()

        size = QSize(150, 20)

        self.__boxLayout.addWidget(self.__plotFrame)

        self.__legendLayout = QVBoxLayout()
        self.__boxLayout.addLayout(self.__legendLayout)

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
        self.__maxSpin.setRange(0, 1000000000)
        self.__maxSpin.valueChanged.connect(self.__reScalePlot)
        self.__vertLayout.addWidget(self.__maxSpin)
        self.__vertLayout.insertSpacing(10, 20)

        self.__minLabel = QLabel("y min")
        self.__minLabel.setFixedSize(size)
        self.__vertLayout.addWidget(self.__minLabel)
        self.__minSpin = QSpinBox()
        self.__minSpin.setFixedSize(size)
        self.__minSpin.setRange(0, 1000000000)
        self.__minSpin.valueChanged.connect(self.__reScalePlot)
        self.__vertLayout.addWidget(self.__minSpin)
        self.__vertLayout.insertSpacing(10, 40)

        self.__typeCombo = QComboBox()
        self.__typeCombo.setFixedSize(size)
        self.__typeCombo.addItems(self.__types)
        self.__vertLayout.addWidget(self.__typeCombo)
        self.__saveButton = QPushButton(QCoreApplication.translate("VDLTools","Save"))
        self.__saveButton.setFixedSize(size)
        self.__saveButton.clicked.connect(self.__save)
        self.__vertLayout.addWidget(self.__saveButton)

        self.__boxLayout.addLayout(self.__vertLayout)

        self.__maxSpin.setEnabled(False)
        self.__minSpin.setEnabled(False)

    def __changePlotWidget(self):
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
            title = QwtText(QCoreApplication.translate("VDLTools","Distance [m]"))
            title.setFont(QFont("Helvetica", 10))
            self.__plotWdg.setAxisTitle(QwtPlot.xBottom, title)
            title.setText(QCoreApplication.translate("VDLTools","Elevation [m]"))
            title.setFont(QFont("Helvetica", 10))
            self.__plotWdg.setAxisTitle(QwtPlot.yLeft, title)
            self.__zoomer = QwtPlotZoomer(QwtPlot.xBottom, QwtPlot.yLeft, QwtPicker.DragSelection, QwtPicker.AlwaysOff,
                                   self.__plotWdg.canvas())
            self.__zoomer.setRubberBandPen(QPen(Qt.blue))
            # self.__plotWdg.insertLegend(QwtLegend())
            grid = Qwt.QwtPlotGrid()
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

            self.__axes = fig.add_axes((0.05, 0.15, 0.92, 0.82))
            self.__axes.set_xbound(0, 1000)
            self.__axes.set_ybound(0, 1000)
            self.__manageMatplotlibAxe(self.__axes)
            self.__plotWdg = FigureCanvasQTAgg(fig)
            sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            self.__plotWdg.setSizePolicy(sizePolicy)
            self.__frameLayout.addWidget(self.__plotWdg)

            # mpltoolbar = NavigationToolbar2QTAgg(self.__plotWdg, self.__plotFrame)
            # self.__frameLayout.addWidget(mpltoolbar)
            # lstActions = mpltoolbar.actions()
            # mpltoolbar.removeAction(lstActions[7])
            # mpltoolbar.removeAction(lstActions[8])

    def setProfiles(self, profiles, numLines):
        self.__numLines = numLines
        self.__profiles = profiles
        if self.__lib == 'Matplotlib':
            self.__prepare_points()

    def drawVertLine(self):
        if (self.__profiles is None) or (len(self.__profiles) == 0):
            return
        profileLen = 0
        self.__profiles[0]['l'] = profileLen
        # self.label(0, 1, 0)
        for i in range(0, len(self.__profiles)-1):
            x1 = float(self.__profiles[i]['x'])
            y1 = float(self.__profiles[i]['y'])
            x2 = float(self.__profiles[i+1]['x'])
            y2 = float(self.__profiles[i+1]['y'])
            profileLen += sqrt(((x2-x1)*(x2-x1)) + ((y2-y1)*(y2-y1)))
            self.__profiles[i+1]['l'] = profileLen

            # zz = []
            # for j in xrange(self.__numLines):
            #     if self.__profiles[i+1]['z'][j] is not None:
            #         zz.append(j)
            # if len(zz) == 2:
            #     width = 3
            # else:
            #     width = 1
            # self.label(i+1,width, profileLen)

    def attachCurves(self, names):
        if (self.__profiles is None) or (self.__profiles == 0):
            return
        colors = [Qt.red, Qt.green, Qt.blue, Qt.cyan, Qt.magenta, Qt.yellow]
        for i in xrange(len(self.__profiles[0]['z'])):
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

            if v < len(colors):
                color = colors[v]
            else:
                d = v / len(colors)
                color = colors[v - int(d * len(colors))]

            if i == 0 or i > (self.__numLines-1):
                legend = QLabel("<font color='" + QColor(color).name() + "'>" + name + "</font>")
                self.__legendLayout.addWidget(legend)

            if self.__lib == 'Qwt5':

                # Split xx and yy into single lines at None values
                xx = [list(g) for k, g in itertools.groupby(xx, lambda x: x is None) if not k]
                yy = [list(g) for k, g in itertools.groupby(yy, lambda x: x is None) if not k]

                # Create & attach one QwtPlotCurve per one single line
                for j in range(len(xx)):
                    curve = QwtPlotCurve(name)
                    curve.setData(xx[j], yy[j])
                    curve.setPen(QPen(color, 3))
                    if i > (self.__numLines-1):
                        curve.setStyle(QwtPlotCurve.NoCurve)
                        symbol = QwtSymbol()
                        symbol.setStyle(QwtSymbol.Ellipse)
                        symbol.setPen(QPen(color, 4))
                        curve.setSymbol(symbol)
                    curve.attach(self.__plotWdg)

            elif self.__lib == 'Matplotlib':
                qcol = QColor(color)
                if i < self.__numLines:
                    self.__plotWdg.figure.get_axes()[0].plot(xx, yy, gid=name, linewidth=3)
                else:
                    self.__plotWdg.figure.get_axes()[0].plot(xx, yy, gid=name, linewidth=5, marker='o',
                                                             linestyle='None')
                tmp = self.__plotWdg.figure.get_axes()[0].get_lines()
                for t in range(len(tmp)):
                    if name == str(tmp[t].get_gid()):
                        tmp[i].set_color((qcol.red() / 255.0, qcol.green() / 255.0, qcol.blue() / 255.0,
                                          qcol.alpha() / 255.0))
                        self.__plotWdg.draw()
                        break

        # scaling this
        try:
            self.__reScalePlot()
        except:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools","Error"),
                QCoreApplication.translate("VDLTools","rescale problem... (trace printed)"),
                level=QgsMessageBar.CRITICAL)
            print(
                QCoreApplication.translate("VDLTools","rescale problem : "), sys.exc_info()[0], traceback.format_exc())
        if self.__lib == 'Qwt5':
            self.__plotWdg.replot()
        elif self.__lib == 'Matplotlib':
            # self.__plotWdg.figure.legend(self.__plotWdg.figure.get_axes()[0].get_lines(), names, 'center left')
            self.__plotWdg.figure.get_axes()[0].redraw_in_frame()
            self.__plotWdg.draw()
            self.__activateMouseTracking(True)
            self.__rubberband.show()

    def __reScalePlot(self):  # called when spinbox value changed
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
        if minimumValue == maximumValue:
            # Automatic mode
            minimumValue = 1000000000
            maximumValue = -1000000000

        for i in range(len(self.__profiles)):
            mini = self.__minTab(self.__profiles[i]['z'])
            if int(mini) < minimumValue:
                minimumValue = int(mini) - 1
            maxi = self.__maxTab(self.__profiles[i]['z'])
            if int(maxi) > maximumValue:
                maximumValue = int(maxi) + 1
        self.__maxSpin.setValue(maximumValue)
        self.__minSpin.setValue(minimumValue)
        self.__maxSpin.setEnabled(True)
        self.__minSpin.setEnabled(True)
        if self.__lib == 'Qwt5':
            rect = QRectF(0, minimumValue,maxi, maximumValue-minimumValue)
            self.__zoomer.setZoomBase(rect)

        for i in xrange(len(self.__profiles)):
            zz = []
            for j in xrange(self.__numLines):
                if self.__profiles[i]['z'][j] is not None:
                    zz.append(j)
            if len(zz) == 2:
                width = 3
            else:
                width = 1

            if self.__lib == 'Qwt5':
                vertLine = QwtPlotMarker()
                vertLine.setLineStyle(QwtPlotMarker.VLine)
                pen = vertLine.linePen()
                pen.setWidth(width)
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
                self.__axes.text(self.__profiles[i]['l'], 375, i)
                self.__plotWdg.figure.get_axes()[0].annotate('ann' + str(i), xy=(self.__profiles[i]['l'], 200))

        if minimumValue < maximumValue:
            if self.__lib == 'Qwt5':
                self.__plotWdg.setAxisScale(0, minimumValue, maximumValue, 0)
                self.__plotWdg.replot()
            elif self.__lib == 'Matplotlib':
                self.__plotWdg.figure.get_axes()[0].set_ybound(minimumValue,maximumValue)
                self.__plotWdg.figure.get_axes()[0].redraw_in_frame()
                self.__plotWdg.draw()

    def __minTab(self, tab):
        mini = 1000000000
        for t in tab:
            if t is None:
                continue
            if t < mini:
                mini = t
        return mini

    def __maxTab(self, tab):
        maxi = -1000000000
        for t in tab:
            if t is None:
                continue
            if t > maxi:
                maxi = t
        return maxi

    def __setLib(self):
        self.__lib = self.__libs[self.__libCombo.currentIndex()]
        self.__changePlotWidget()

    def __save(self):
        idx = self.__typeCombo.currentIndex()
        if idx == 0:
            self.__outPDF()
        elif idx == 1:
            self.__outPNG()
        elif idx == 2:
            self.__outSVG()
        elif idx == 3:
            self.__outPrint()
        else:
            self.__iface.messageBar().pushMessage(
                QCoreApplication.translate("VDLTools","Error"),
                QCoreApplication.translate("VDLTools","Invalid index ") + str(idx),
                level=QgsMessageBar.CRITICAL)

    def __outPrint(self): # Postscript file rendering doesn't work properly yet.
        fileName = QFileDialog.getSaveFileName(
            self.__iface.mainWindow(), QCoreApplication.translate("VDLTools","Save As"),
            QCoreApplication.translate("VDLTools", "Profile of curve.ps"),"PostScript Format (*.ps)")
        if fileName:
            if self.__lib == 'Qwt5':
                printer = QPrinter()
                printer.setCreator(QCoreApplication.translate("VDLTools","QGIS Profile Plugin"))
                printer.setDocName(QCoreApplication.translate("VDLTools","QGIS Profile"))
                printer.setOutputFileName(fileName)
                printer.setColorMode(QPrinter.Color)
                printer.setOrientation(QPrinter.Portrait)
                dialog = QPrintDialog(printer)
                if dialog.exec_():
                    self.__plotWdg.print_(printer)
            elif self.__lib == 'Matplotlib':
                self.__plotWdg.figure.savefig(str(fileName))

    def __outPDF(self):
        fileName = QFileDialog.getSaveFileName(
            self.__iface.mainWindow(), QCoreApplication.translate("VDLTools","Save As"),
            QCoreApplication.translate("VDLTools","Profile of curve.pdf"),"Portable Document Format (*.pdf)")
        if fileName:
            if self.__lib == 'Qwt5':
                printer = QPrinter()
                printer.setCreator(QCoreApplication.translate("VDLTools","QGIS Profile Plugin"))
                printer.setOutputFileName(fileName)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOrientation(QPrinter.Landscape)
                self.__plotWdg.print_(printer)
            elif self.__lib == 'Matplotlib':
                self.__plotWdg.figure.savefig(str(fileName))

    def __outSVG(self):
        fileName = QFileDialog.getSaveFileName(
            self.__iface.mainWindow(), QCoreApplication.translate("VDLTools","Save As"),
            QCoreApplication.translate("VDLTools","Profile of curve.svg"), "Scalable Vector Graphics (*.svg)")
        if fileName:
            if self.__lib == 'Qwt5':
                printer = QSvgGenerator()
                printer.setFileName(fileName)
                printer.setSize(QSize(800, 400))
                self.__plotWdg.print_(printer)
            elif self.__lib == 'Matplotlib':
                self.__plotWdg.figure.savefig(str(fileName))

    def __outPNG(self):
        fileName = QFileDialog.getSaveFileName(
            self.__iface.mainWindow(), QCoreApplication.translate("VDLTools","Save As"),
            QCoreApplication.translate("VDLTools","Profile of curve.png"),"Portable Network Graphics (*.png)")
        if fileName:
            if self.__lib == 'Qwt5':
                QPixmap.grabWidget(self.__plotWdg).save(fileName, "PNG")
            elif self.__lib == 'Matplotlib':
                self.__plotWdg.figure.savefig(str(fileName))

    def clearData(self):  # erase one of profiles
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
        axe.grid()
        axe.tick_params(axis="both", which="major", direction="out", length=10, width=1, bottom=True, top=False,
                         left=True, right=False)
        axe.minorticks_on()
        axe.tick_params(axis="both", which="minor", direction="out", length=5, width=1, bottom=True, top=False,
                         left=True, right=False)

    def __activateMouseTracking(self, activate):
        if activate:
            self.__doTracking = True
            self.__loadRubber()
            self.cid = self.__plotWdg.mpl_connect('motion_notify_event', self.__mouseevent_mpl)
        elif self.__doTracking:
            self.__doTracking = False
            self.__plotWdg.mpl_disconnect(self.cid)
            if self.__rubberband:
                self.__canvas.scene().removeItem(self.__rubberband)
            try:
                if self.__vline is not None:
                    self.__plotWdg.figure.get_axes()[0].lines.remove(self.__vline)
                    self.__plotWdg.draw()
            except Exception, e:
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools","Error"),
                    QCoreApplication.translate("VDLTools","Tracking exception..."), level=QgsMessageBar.CRITICAL)
                print str(e)

    def __mouseevent_mpl(self, event):
        if event.xdata:
            try:
                if self.__vline is not None:
                    self.__plotWdg.figure.get_axes()[0].lines.remove(self.__vline)
            except Exception, e:
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools","Error"),
                    QCoreApplication.translate("VDLTools","Mouse event exception..."), level=QgsMessageBar.CRITICAL)
                print str(e)
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
            self.__rubberband.show()
            point = QgsPoint(x, y)
            self.__rubberband.setCenter(point)

    def __loadRubber(self):
        self.__rubberband = QgsVertexMarker(self.__canvas)
        self.__rubberband.setIconSize(5)
        self.__rubberband.setIconType(QgsVertexMarker.ICON_BOX)  # or ICON_CROSS, ICON_X
        self.__rubberband.setPenWidth(3)

    def __prepare_points(self):
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
        if self.__maxSpin is not None:
            self.__maxSpin.valueChanged.disconnect(self.__reScalePlot)
            self.__maxSpin = None
        if self.__minSpin is not None:
            self.__minSpin.valueChanged.disconnect(self.__reScalePlot)
            self.__minSpin = None
        if self.__saveButton is not None:
            self.__saveButton.clicked.disconnect(self.__save)
            self.__saveButton = None
        if self.__libCombo is not None:
            self.__libCombo.currentIndexChanged.disconnect(self.__setLib)
            self.__libCombo = None
        if QDockWidget is not None:
            QDockWidget.closeEvent(self, event)
