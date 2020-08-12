# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2016-04-05
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
from builtins import object
from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

from .tools.intersect_tool import IntersectTool
from .tools.profile_tool import ProfileTool
from .tools.interpolate_tool import InterpolateTool
from .tools.extrapolate_tool import ExtrapolateTool
from .tools.show_settings import ShowSettings
from .tools.import_measures import ImportMeasures
from .tools.subprofile_tool import SubProfileTool
from .tools.pointer_tool import PointerTool
from .tools.control_tool import ControlTool
from .tools.drawndown_tool import DrawdownTool
from .tools.orientation_tool import OrientationTool

# Initialize Qt resources from file resources.py
from . import resources

import os


class VDLTools(object):
    """
    Main plugin class
    """
    MORE_TOOLS = False

    def __init__(self, iface):
        """Constructor
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.mapCanvas = iface.mapCanvas()
        self.intersectTool = None
        self.profileTool = None
        self.subProfileTool = None
        self.drawdownTool = None
        self.pointerTool = None
        self.showSettings = None
        self.controlTool = None
        self.orientationTool = None
        if VDLTools.MORE_TOOLS:
            self.importMeasures = None

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'VDLTools_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = QCoreApplication.translate("VDLTools", "&VDL Tools")
        self.toolbar = self.iface.addToolBar("VDLTools")
        self.toolbar.setObjectName("VDLTools")

    def add_action(self, tool, parent, enable=True, isMapTool=True, inToolBar=True):
        """To add an available action.
        :param tool: the tool linked to the action
        :param parent: the interface main window
        :param enable: if the action is enabled at the beginning
        :param isMapTool: if the action is a map tool or not
        :param inToolBar: if the action has to be in the menu with an icon
        :return: the added action
        """

        icon = QIcon(tool.icon_path)
        action = QAction(icon, tool.text, parent)

        if isMapTool:
            tool.setAction(action)
            action.triggered.connect(tool.setTool)
            action.setEnabled(enable)
        else:
            action.triggered.connect(tool.start)
        action.setCheckable(True)
        if inToolBar:
            self.toolbar.addAction(action)

        self.iface.addPluginToMenu(
            self.menu,
            action)
        self.actions.append(action)
        return action

    def initGui(self):
        """
        Create the menu entries and toolbar icons inside the QGIS GUI
        """

        self.showSettings = ShowSettings(self.iface, self.MORE_TOOLS)
        self.add_action(self.showSettings, self.iface.mainWindow(), True, False, False)
        self.intersectTool = IntersectTool(self.iface)
        self.add_action(self.intersectTool, self.iface.mainWindow())
        self.profileTool = ProfileTool(self.iface)
        self.add_action(self.profileTool, self.iface.mainWindow(), False)
        self.subProfileTool = SubProfileTool(self.iface)
        self.add_action(self.subProfileTool, self.iface.mainWindow())
        self.pointerTool = PointerTool(self.iface)
        self.add_action(self.pointerTool, self.iface.mainWindow())
        self.interpolateTool = InterpolateTool(self.iface)
        self.add_action(self.interpolateTool, self.iface.mainWindow(), False)
        self.extrapolateTool = ExtrapolateTool(self.iface)
        self.add_action(self.extrapolateTool, self.iface.mainWindow(), False)
        self.drawdownTool = DrawdownTool(self.iface)
        self.add_action(self.drawdownTool, self.iface.mainWindow())
        self.controlTool = ControlTool(self.iface)
        self.add_action(self.controlTool, self.iface.mainWindow())
        self.orientationTool = OrientationTool(self.iface)
        self.add_action(self.orientationTool, self.iface.mainWindow())

        self.intersectTool.ownSettings = self.showSettings
        self.profileTool.ownSettings = self.showSettings
        self.subProfileTool.ownSettings = self.showSettings
        self.drawdownTool.ownSettings = self.showSettings
        self.controlTool.ownSettings = self.showSettings
        self.orientationTool.ownSettings = self.showSettings

        self.profileTool.setEnable(self.iface.activeLayer())
        self.iface.currentLayerChanged.connect(self.profileTool.setEnable)
        self.interpolateTool.setEnable(self.iface.activeLayer())
        self.iface.currentLayerChanged.connect(self.interpolateTool.setEnable)
        self.extrapolateTool.setEnable(self.iface.activeLayer())
        self.iface.currentLayerChanged.connect(self.extrapolateTool.setEnable)
        self.drawdownTool.setEnable()
        self.showSettings.changedSignal.connect(self.drawdownTool.setEnable)

        if VDLTools.MORE_TOOLS:
            self.importMeasures = ImportMeasures(self.iface)
            self.add_action(self.importMeasures, self.iface.mainWindow(), isMapTool=False)

            self.importMeasures.ownSettings = self.showSettings

    def unload(self):
        """
        Removes the plugin menu item and icon from QGIS GUI
        """
        for action in self.actions:
            self.iface.removePluginMenu(
                QCoreApplication.translate("VDLTools", "&VDL Tools"),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
