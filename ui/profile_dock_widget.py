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
                         QPixmap,
                         QFileDialog,
                         QPrintDialog,
                         QSizePolicy,
                         QPrinter)
from PyQt4.QtCore import (QSize,
                          QRectF,
                          Qt)
from PyQt4.QtSvg import QSvgGenerator
from PyQt4.Qwt5 import (QwtPlot,
                        QwtPlotZoomer,
                        QwtPicker,
                        QwtPlotItem,
                        Qwt,
                        QwtPlotMarker,
                        QwtPlotCurve)
import itertools
import sys
from math import sqrt


class ProfileDockWidget(QDockWidget):
    def __init__(self, iface):
        QDockWidget.__init__(self)
        self.setWindowTitle("Profile Tool")
        self.resize(1024, 400)
        self.__iface = iface
        self.__types = ['PDF', 'PNG', 'SVG', 'PS']

        self.__profiles = None

        self.__contentWidget = QWidget()
        self.setWidget(self.__contentWidget)

        self.__boxLayout = QHBoxLayout()
        self.__contentWidget.setLayout(self.__boxLayout)

        self.__plotFrame = QFrame()
        self.__frameLayout = QHBoxLayout()
        self.__plotFrame.setLayout(self.__frameLayout)

        self.__plotWdg = QwtPlot(self.__plotFrame)

        self.__frameLayout.addWidget(self.__plotWdg)
        # self.__plotWdg.setGeometry(1, 1, 1000, 200)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        self.__plotWdg.setSizePolicy(sizePolicy)
        self.__plotWdg.setAutoFillBackground(False)
        # Decoration
        self.__plotWdg.setCanvasBackground(Qt.white)
        self.__plotWdg.plotLayout().setAlignCanvasToScales(True)
        self.__plotWdg.plotLayout().setSpacing(100)
        self.__zoomer = QwtPlotZoomer(QwtPlot.xBottom, QwtPlot.yLeft, QwtPicker.DragSelection, QwtPicker.AlwaysOff,
                               self.__plotWdg.canvas())
        self.__zoomer.setRubberBandPen(QPen(Qt.blue))
        grid = Qwt.QwtPlotGrid()
        grid.setPen(QPen(QColor('grey'), 0, Qt.DotLine))
        grid.attach(self.__plotWdg)

        size = QSize(150, 20)

        self.__boxLayout.addWidget(self.__plotFrame)

        self.__vertLayout = QVBoxLayout()
        self.__maxLabel = QLabel("maximum")
        self.__maxLabel.setFixedSize(size)
        self.__vertLayout.addWidget(self.__maxLabel)
        self.__maxSpin = QSpinBox()
        self.__maxSpin.setFixedSize(size)
        self.__maxSpin.setRange(0, 1000000000)
        self.__maxSpin.valueChanged.connect(self.__reScalePlot)
        self.__vertLayout.addWidget(self.__maxSpin)
        self.__vertLayout.insertSpacing(10, 20)

        self.__minLabel = QLabel("minimum")
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
        self.__saveButton = QPushButton("Save")
        self.__saveButton.setFixedSize(size)
        self.__saveButton.clicked.connect(self.__save)
        self.__vertLayout.addWidget(self.__saveButton)

        self.__boxLayout.addLayout(self.__vertLayout)

        self.__maxSpin.setEnabled(False)
        self.__minSpin.setEnabled(False)

    def setProfiles(self, profiles):
        self.__profiles = profiles

    def drawVertLine(self):
        if (self.__profiles is None) or (self.__profiles == 0):
            return
        profileLen = 0
        self.__profiles[0]['l'] = profileLen
        for i in range(0, len(self.__profiles)-1):
            x1 = float(self.__profiles[i]['x'])
            y1 = float(self.__profiles[i]['y'])
            x2 = float(self.__profiles[i+1]['x'])
            y2 = float(self.__profiles[i+1]['y'])
            profileLen += sqrt (((x2-x1)*(x2-x1)) + ((y2-y1)*(y2-y1)))
            self.__profiles[i+1]['l'] = profileLen
            vertLine = QwtPlotMarker()
            vertLine.setLineStyle(QwtPlotMarker.VLine)
            vertLine.setXValue(profileLen)
            vertLine.attach(self.__plotWdg)

    def attachCurves(self):
        name = "curve"
        if (self.__profiles is None) or (self.__profiles == 0):
            return
        xx = []
        yy = []
        for prof in self.__profiles:
            xx.append(prof['l'])
            yy.append(prof['z'])

        for j in range(len(yy)):
            if yy[j] is None:
                xx[j] = None

        # Split xx and yy into single lines at None values
        xx = [list(g) for k, g in itertools.groupby(xx, lambda x: x is None) if not k]
        yy = [list(g) for k, g in itertools.groupby(yy, lambda x: x is None) if not k]

        # Create & attach one QwtPlotCurve per one single line
        for j in range(len(xx)):
            curve = QwtPlotCurve(name)
            curve.setData(xx[j], yy[j])
            curve.setPen(QPen(Qt.red, 3))
            curve.attach(self.__plotWdg)

        #scaling this
        try:
            self.__reScalePlot()
        except:
            print("rescale problem : ", sys.exc_info()[0])
        self.__plotWdg.replot()

    def __reScalePlot(self):  # called when spinbox value changed
        if (self.__profiles is None) or (self.__profiles == 0):
            self.__plotWdg.replot()
            return

        maxi = 0
        for i in range(len(self.__profiles)):
            if (int(self.__profiles[i]['l'])) > maxi:
                maxi = int(self.__profiles[i]['l']) + 1
        print(maxi)
        self.__plotWdg.setAxisScale(2, 0, maxi, 0)

        minimumValue = self.__minSpin.value()
        maximumValue = self.__maxSpin.value()
        print(minimumValue, maximumValue)
        if minimumValue == maximumValue:
            # Automatic mode
            minimumValue = 1000000000
            maximumValue = -1000000000

            for i in range(len(self.__profiles)):
                if int(self.__profiles[i]['z']) < minimumValue:
                    minimumValue = int(self.__profiles[i]['z']) - 1
                if int(self.__profiles[i]['z']) > maximumValue:
                    maximumValue = int(self.__profiles[i]['z']) + 1
            print(minimumValue)
            print(maximumValue)
            self.__maxSpin.setValue(maximumValue)
            self.__minSpin.setValue(minimumValue)
            self.__maxSpin.setEnabled(True)
            self.__minSpin.setEnabled(True)
            rect = QRectF(0, minimumValue,maxi, maximumValue-minimumValue)
            self.__zoomer.setZoomBase(rect)

        if minimumValue < maximumValue:
            self.__plotWdg.setAxisScale(0, minimumValue, maximumValue, 0)
            self.__plotWdg.replot()

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
            print('plottingtool: invalid index ' + str(idx))

    def __outPrint(self): # Postscript file rendering doesn't work properly yet.
        fileName = QFileDialog.getSaveFileName(self.__iface.mainWindow(), "Save As","Profile of curve.ps","PostScript Format (*.ps)")
        if fileName:
            printer = QPrinter()
            printer.setCreator("QGIS Profile Plugin")
            printer.setDocName("QGIS Profile")
            printer.setOutputFileName(fileName)
            printer.setColorMode(QPrinter.Color)
            printer.setOrientation(QPrinter.Portrait)
            dialog = QPrintDialog(printer)
            if dialog.exec_():
                self.__plotWdg.print_(printer)

    def __outPDF(self):
        fileName = QFileDialog.getSaveFileName(self.__iface.mainWindow(), "Save As","Profile of curve.pdf","Portable Document Format (*.pdf)")
        if fileName:
            printer = QPrinter()
            printer.setCreator('QGIS Profile Plugin')
            printer.setOutputFileName(fileName)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOrientation(QPrinter.Landscape)
            self.__plotWdg.print_(printer)

    def __outSVG(self):
        fileName = QFileDialog.getSaveFileName(self.__iface.mainWindow(), "Save As","Profile of curve.svg","Scalable Vector Graphics (*.svg)")
        if fileName:
            printer = QSvgGenerator()
            printer.setFileName(fileName)
            printer.setSize(QSize(800, 400))
            self.__plotWdg.print_(printer)

    def __outPNG(self):
        fileName = QFileDialog.getSaveFileName(self.__iface.mainWindow(), "Save As","Profile of curve.png","Portable Network Graphics (*.png)")
        if fileName:
            QPixmap.grabWidget(self.__plotWdg).save(fileName, "PNG")

    def clearData(self):  # erase one of profiles
        if self.__profiles is None:
            return
        self.__plotWdg.clear()
        self.__profiles = None
        temp1 = self.__plotWdg.itemList()
        for j in range(len(temp1)):
            if temp1[j].rtti() == QwtPlotItem.Rtti_PlotCurve:
                temp1[j].detach()
        self.__maxSpin.setEnabled(False)
        self.__minSpin.setEnabled(False)
        self.__maxSpin.setValue(0)
        self.__minSpin.setValue(0)

    def closeEvent(self, event):
        self.__maxSpin.valueChanged.disconnect()
        self.__minSpin.valueChanged.disconnect()
        self.__saveButton.clicked.disconnect()
        if QDockWidget is not None:
            QDockWidget.closeEvent(self, event)
