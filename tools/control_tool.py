# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VDLTools
                                 A QGIS plugin for the Ville de Lausanne
                              -------------------
        begin                : 2017-08-21
        git sha              : $Format:%H$
        copyright            : (C) 2016 Ville de Lausanne
        author               : Daniel Savary
        email                : daniel.savary@lausanne.ch
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
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QProgressBar
from .area_tool import AreaTool
from ..ui.choose_control_dialog import ChooseControlDialog
from qgis.core import (Qgis,
                       QgsVectorLayer,
                       QgsDataSourceUri,
                       QgsFeatureRequest,
                       QgsProject,
                       QgsWkbTypes)
from ..core.db_connector import DBConnector
from datetime import datetime


class ControlTool(AreaTool):
    """
    Map tool class to make control request
    """

    def __init__(self, iface):
        """
        Constructor
        :param iface: interface
        """
        AreaTool.__init__(self, iface)
        self.__iface = iface
        self.icon_path = ':/plugins/VDLTools/icons/control_icon.png'
        self.text = QCoreApplication.translate("VDLTools", "Make control requests on selected area")
        self.releasedSignal.connect(self.__released)
        self.__chooseDlg = None
        self.__db = None
        self.ownSettings = None
        self.__crs = None
        self.__registry = QgsProject.instance()                 # définition du registre des couches dans le projet
        self.__configTable = None                               # nom de la table dans la base de données qui liste
                                                                # tous les contrôles possible
        self.__schemaDb = None
        self.__layerCfgControl = None                           # nom de la couche dans le projet qui correspond à la
                                                                # table de la liste des contrôles
        self.__lrequests = []                                   # liste des requêtes actives
        self.areaMax = 1000000                                  # tolérance de surface max. pour lancer un contrôle

    def setTool(self):
        """
        To set the current tool as this one
        """
        self.canvas().setMapTool(self)

    def __released(self):
        """
        When selection is complete
        """
        if self.ownSettings is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "No settings given !!"),
                                                  level=Qgis.Critical, duration=0)
            return
        if self.ownSettings.controlUriDb is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "No control db given !!"),
                                                  level=Qgis.Critical, duration=0)
            return
        if self.ownSettings.controlSchemaDb is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "No control db schema given !!"),
                                                  level=Qgis.Critical, duration=0)
            return
        if self.ownSettings.controlConfigTable is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "No control config table given !!"),
                                                  level=Qgis.Critical, duration=0)
            return

        self.__configTable = self.ownSettings.controlConfigTable
        self.__schemaDb = self.ownSettings.controlSchemaDb

        self.connector = DBConnector(self.ownSettings.controlUriDb, self.__iface)
        self.__db = self.connector.setConnection()
        """
        Test si la couche / table qui contient l'ensemble des contrôles existe bien dans le projet
        """
        if self.__db is not None:
            uricfg = QgsDataSourceUri()
            uricfg.setConnection(self.__db.hostName(),str(self.__db.port()), self.__db.databaseName(),
                                 self.__db.userName(),self.__db.password())
            uricfg.setDataSource(self.__schemaDb,self.__configTable,None,"","id")
            self.__layerCfgControl = QgsVectorLayer(uricfg.uri(),"Liste des contrôles", "postgres")
                    # définition d'une couche QMapLayer au niveau QGIS

        """
        Test si la zone de contrôle a bien été définie par l'utilisateur
        """

        if self.geom is None:
             self.__iface.messageBar().pushMessage(
                 QCoreApplication.translate("VDLTools", "Request Area not defined, ") +
                 QCoreApplication.translate("VDLTools", "please define a control area (maintain mouse clic)")
                 , level=Qgis.Critical, duration=5)
        else:
            if self.geom.area() > self.areaMax:
                self.__iface.messageBar().pushMessage(
                    QCoreApplication.translate("VDLTools", "Please define a smaller control area, max = 1 km2"),
                    level=Qgis.Critical, duration=5)
            else:
                """
                Liste des contrôles actifs existants
                """
                req = QgsFeatureRequest().setFilterExpression('"active" is true')
                for f in self.__layerCfgControl.getFeatures(req):
                    lrequests = {}
                    lrequests["id"]=str(f["id"])
                    lrequests["name"]=f["layer_name"]
                    lrequests["code"]=f["code_error"]
                    lrequests["check"]=f["check_defaut"]
                    self.__lrequests.append(lrequests)
                # trier la liste de dictionnaire
                self.__lrequests = sorted( self.__lrequests,key=lambda k: int(k['id']))

                self.__chooseDlg = ChooseControlDialog(self.__lrequests)
                self.__chooseDlg.okButton().clicked.connect(self.__onOk)
                self.__chooseDlg.cancelButton().clicked.connect(self.__onCancel)
                self.__chooseDlg.show()

    def __onCancel(self):
        """
        When the Cancel button in Choose Control Dialog is pushed
        """
        self.__chooseDlg.reject()
        self.__cancel()

    def __onOk(self):
        """
        When the Ok button in Choose Control Dialog is pushed
        """
        self.__chooseDlg.accept()

        if self.__db is not None and self.geom.area() > 0:
            if len(self.__chooseDlg.controls()) == 0:
                self.__iface.messageBar().pushMessage(
                    "Avertissement",
                    QCoreApplication.translate("VDLTools", "No control selected"),
                    level=Qgis.Info, duration=5)
            else:
                self.__createCtrlLayers(self.__chooseDlg.controls())
            self.__cancel()
        else:
            self.__iface.messageBar().pushMessage(
                "Avertissement",
                QCoreApplication.translate("VDLTools", "Database onnection problem, or too small area"),
                level=Qgis.Info, duration=5)

    def __createCtrlLayers(self,requete):
        """
        Création des couches de contrôles
        - selon une requête SQL dans la base de données (choix  ou des contrôle par l'utilisateur)
        - selon une zone géographique définie par l'utilisateur
        :param requete: liste des requêtes
        """

        self.__iface.messageBar().clearWidgets()
        progressMessageBar = self.__iface.messageBar()
                # ajout d'une barre de progression pour voir le chargement progressif des couches
        progress = QProgressBar()
        progress.setMaximum(100)
        progressMessageBar.pushWidget(progress)

        # récupérer la géométrie définie par l'utilisateur pour l'utiliser dans les requêtes SQL
        # conversion en géométrie binaire et dans le bon système de coordonnée)
        self.__crs = self.__iface.mapCanvas().mapSettings().destinationCrs().postgisSrid()
                # défintion du système de coordonnées en sortie (par défaut 21781), récupérer des paramètres du projets
        bbox = "(SELECT ST_GeomFromText('" + self.geom.asWkt() + "'," + str(self.__crs) + "))"

        # paramètres de la source des couches à ajouter au projet
        uri = QgsDataSourceUri()
        uri.setConnection(self.__db.hostName(),str(self.__db.port()), self.__db.databaseName(),
                          self.__db.userName(),self.__db.password())
        uri.setSrid(str(self.__crs))
        outputLayers = []       # listes des couches de résultats à charger dans le projet
        styleLayers = []        # listes des styles de couches (fichier qml)
        i = 0
        totalError = 0          # décompte des erreurs détectées (nombre d'objets dans chaque couche)
        for name in requete:
            for q in self.__layerCfgControl.getFeatures(QgsFeatureRequest(int(name))):
                query_fct = q["sql_function"]
                query_fct = query_fct.replace("bbox",bbox)
                geom_type = QgsWkbTypes.parseType(q["geom_type"])
                    # récupérer le type de géométrie QGIS "QgsWKBTypes" depuis un type de géométrie WKT Postgis
                uri.setWkbType(geom_type)
                uri.setDataSource('',query_fct,q["geom_name"],"",q["key_attribute"])
                layer = QgsVectorLayer(uri.uri(),q["layer_name"], "postgres")

                totalError = totalError + layer.featureCount()
                if layer.featureCount() > 0:
                    outputLayers.append(layer)
                    styleLayers.append(str(q["layer_style"]))
            percent = (float(i+1.0)/float(len(requete))) * 100    # Faire évoluer la barre de progression du traitement
            progress.setValue(percent)
            i += 1
        if len(outputLayers) > 0:
            self.__addCtrlLayers(outputLayers, styleLayers)
            self.__iface.messageBar().clearWidgets()
            self.__iface.messageBar().pushMessage(
                "Info",
                QCoreApplication.translate("VDLTools", "All layers have been charged with success in the projet. |") +
                QCoreApplication.translate("VDLTools", "Total errors : ") +
                        str(totalError), level=Qgis.Info, duration=10)
        else:
            self.__iface.messageBar().clearWidgets()
            self.__iface.messageBar().pushMessage(
                "Info",
                QCoreApplication.translate("VDLTools", "Good !! No error detected on the defined area"),
                level=Qgis.Info, duration=5)

    def __addCtrlLayers(self, layers, styles):
        """
        Ajout des couches du résultats des requêtes de contrôles
        :param layers: Liste des couches à ajouter au projet
        :param styles: Liste des styles de couches
        """

        groupName = 'CONTROL (' +datetime.now().strftime("%Y-%m-%d")+')'
                # définir le nom du groupe dans lequel seront ajouté chaque couche
        project_tree = QgsProject.instance().layerTreeRoot()             # arbre des couches
        if project_tree.findGroup(groupName) is None:
            ctrl_group = project_tree.insertGroup(0,groupName)
        else:
            ctrl_group = project_tree.findGroup(groupName)
            ctrl_group.removeAllChildren()                          # effacer les couches existantes prend du temps !!

        for i in range(0,len(layers)):
            layers[i].loadNamedStyle(styles[i])
            QgsProject.instance().addMapLayer(layers[i],False)
            ctrl_group.insertLayer(i,layers[i])
        self.__iface.mapCanvas().refresh()                              # rafraîchir la carte


    def __cancel(self):
        """
        To cancel used variables
        """
        self.__chooseDlg = None
        self.__db.close()
        self.geom = None # supprimer la géométrie définie
        self.__lrequests = [] # vider la liste des requêtes actives
