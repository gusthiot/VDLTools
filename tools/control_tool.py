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
from __future__ import division
from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QProgressBar
from .area_tool import AreaTool
from ..ui.choose_control_dialog import ChooseControlDialog
from qgis.gui import QgsMessageBar
from qgis.core import (QgsMapLayerRegistry,
                       QgsVectorLayer,
                       QgsDataSourceURI,
                       QgsFeatureRequest,
                       QgsProject,
                       QgsWKBTypes)
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
        self.__registry = QgsMapLayerRegistry.instance()        # définition du registre des couches dans le projet
        self.__configTable = None                                 # nom de la table dans la base de données qui liste tous les contrôles possible
        self.__schemaDb = None
        self.__layerCfgControl = None                           # nom de la couche dans le projet qui correspond à la table de la liste des contrôles
        self.__lrequests = []                                   # liste des requêtes actives
        self.areaMax = 1000000                                  # tolérance de surface max. pour lancer un contrôle

    def toolName(self):
        """
        To get the tool name
        :return: tool name
        """
        return QCoreApplication.translate("VDLTools", "Control")

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
                                                  level=QgsMessageBar.CRITICAL, duration=0)
            return
        if self.ownSettings.controlUriDb is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "No control db given !!"),
                                                  level=QgsMessageBar.CRITICAL, duration=0)
            return
        if self.ownSettings.controlConfigTable is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "No control table given !!"),
                                                  level=QgsMessageBar.CRITICAL, duration=0)
            return
        if self.ownSettings.controlConfigTable is None:
            self.__iface.messageBar().pushMessage(QCoreApplication.translate("VDLTools", "No config table given !!"),
                                                  level=QgsMessageBar.CRITICAL, duration=0)
            return

        self.__configTable = self.ownSettings.configTable
        self.__schemaDb = self.ownSettings.schemaDb

        self.connector = DBConnector(self.ownSettings.uriDb, self.__iface)
        self.db = self.connector.setConnection()
        """
        Test si la couche / table qui contient l'ensemble des contrôles existe bien dans le projet
        """
        if self.db is not None:
            uricfg = QgsDataSourceURI()
            uricfg.setConnection(self.db.hostName(),str(self.db.port()), self.db.databaseName(),self.db.userName(),self.db.password())
            uricfg.setDataSource(self.__schemaDb,self.__configTable,None,"","id")
            self.__layerCfgControl = QgsVectorLayer(uricfg.uri(),u"Liste des contrôles", "postgres")  #définition d'une couche QMapLayer au niveau QGIS

            '''
            # par requête SQL sans définir de couche avec l'API QGIS
            query = self.db.exec_("""SELECT * FROM """+ self.__schemaDb+ """.""" + self.__configTable + """ WHERE active is true ORDER BY 1""")
            while query.next():
                print query.value(0)
            '''

        """
        Test si la zone de contrôle a bien été définie par l'utilisateur
        """

        if self.geom is None:
             self.__iface.messageBar().pushMessage(u"zone de requête non définie, Veuillez définir une zone de contrôle (maintenir le clic de la souris)", level=QgsMessageBar.CRITICAL, duration=5)
        else:
            #print self.geom.area()
            if self.geom.area() > self.areaMax:
                self.__iface.messageBar().pushMessage(u"Veuillez définir une zone de contrôle plus petite , max. = 1 km2", level=QgsMessageBar.CRITICAL, duration=5)

                """
                Question à l'utilisateur s'il veut continuer ou pas par rapport à une zone de contrôle hors tolérance
                """
                """
                qstBox = QMessageBox()
                qstText = u"Voulez-vous quand même continuer ??, le traitement peut prendre plusieurs minutes, voire plusieurs heures "
                qstBox.setText(qstText)
                qstBox.setWindowTitle(u"Zone de contrôle trop grande")
                qstBox.setIcon(QMessageBox.Question)
                qstBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                repArea = qstBox.exec_()
                # print qstBox.clickedButton().text() # retourne le texte du bouton cliqué
                #bb = qstBox.clickedButton() # role du bouton cliqué (objet)
                repMaxArea = qstBox.buttonRole(qstBox.clickedButton())
                if repMaxArea == 0:
                    print u"on continue malgré tout le traitement"
                elif repMaxArea == 1:
                    print u"on arrête le traitement"
                #print repArea # réponse donnée par la touche cliqué sur la boite de dialogue
                """
            else:
                """
                Liste des contrôles actifs existants
                """
                req = QgsFeatureRequest().setFilterExpression('"active" is true')
                for f in self.__layerCfgControl.getFeatures(req):
                    lrequests = {}
                    lrequests["id"]=str(f[u"id"])
                    lrequests["name"]=f[u"layer_name"]
                    lrequests["code"]=f[u"code_error"]
                    lrequests["check"]=f[u"check_defaut"]
                    self.__lrequests.append(lrequests)
                # trier la liste de dictionnaire
                self.__lrequests = sorted( self.__lrequests,key=lambda k: int(k['id']))
                #print self.__lrequests

                self.__chooseDlg = ChooseControlDialog(self.__lrequests)
                self.__chooseDlg.okButton().clicked.connect(self.__onOk)
                self.__chooseDlg.cancelButton().clicked.connect(self.__onCancel)
                self.__chooseDlg.show()

    def __onCancel(self):
        """
        When the Cancel button in Choose Control Dialog is pushed
        """
        self.__chooseDlg.reject()
        self.geom = None # supprimer la géométrie définie
        self.__lrequests = [] # vider la liste des requêtes actives

    def __onOk(self):
        """
        When the Ok button in Choose Control Dialog is pushed
        """
        self.__chooseDlg.accept()

        self.__connector = DBConnector(self.ownSettings.uriDb, self.__iface)
        self.__db = self.__connector.setConnection()

        if self.__db is not None and self.geom.area() > 0:
            if len(self.__chooseDlg.controls()) == 0:
                self.__iface.messageBar().pushMessage("Avertissement", u"Aucun contrôle sélectionné ", level=QgsMessageBar.INFO, duration=5)
            else:
                self.__createCtrlLayers(self.__chooseDlg.controls())
            self.__cancel()
        else:
            self.__iface.messageBar().pushMessage("Avertissement", u"Problème de connexion à la base de données ou surface trop petite ", level=QgsMessageBar.INFO, duration=5)

    def __createCtrlLayers(self,requete):
        """
        Création des couches de contrôles
        - selon une requête SQL dans la base de données (choix  ou des contrôle par l'utilisateur)
        - selon une zone géographique définie par l'utilisateur
        :param requete: liste des requêtes
        :return:
        """

        self.__iface.messageBar().clearWidgets()
        progressMessageBar = self.__iface.messageBar()                  # ajout d'une barre de progression pour voir le chargement progressif des couches
        progress = QProgressBar()
        progress.setMaximum(100)
        progressMessageBar.pushWidget(progress)

        # récupérer la géométrie définie par l'utilisateur pour l'utiliser dans les requêtes SQL , conversion en géométrie binaire et dans le bon système de coordonnée)
        self.__crs = self.__iface.mapCanvas().mapSettings().destinationCrs().postgisSrid() # défintion du système de coordonnées en sortie (par défaut 21781), récupérer des paramètres du projets
        bbox = "(SELECT ST_GeomFromText('" + self.geom.exportToWkt() + "'," + str(self.__crs) + "))"

        # paramètres de la source des couches à ajouter au projet
        uri = QgsDataSourceURI()
        uri.setConnection(self.__db.hostName(),str(self.__db.port()), self.__db.databaseName(),self.__db.userName(),self.__db.password())
        uri.setSrid(str(self.__crs))
        outputLayers = [] # listes des couches de résultats à charger dans le projet
        styleLayers = []       # listes des styles de couches (fichier qml)
        i = 0
        totalError = 0                                                  # décompte des erreurs détectées (nombre d'objets dans chaque couche)
        for name in requete:
            for q in self.__layerCfgControl.getFeatures(QgsFeatureRequest(int(name))):
                query_fct = q[u"sql_function"]
                query_fct = query_fct.replace("bbox",bbox)
                geom_type = QgsWKBTypes.parseType(q[u"geom_type"])      # récupérer le type de géométrie QGIS "QgsWKBTypes" depuis un type de géométrie WKT Postgis
                uri.setWkbType(geom_type)
                uri.setDataSource('',query_fct,q[u"geom_name"],"",q[u"key_attribute"])
                layer = QgsVectorLayer(uri.uri(),q[u"layer_name"], "postgres")

                totalError = totalError + layer.featureCount()
                if layer.featureCount() > 0:
                    outputLayers.append(layer)
                    styleLayers.append(str(q[u"layer_style"]))
            percent = (float(i+1.0)/float(len(requete))) * 100           # Faire évoluer la barre de progression du traitement
            progress.setValue(percent)
            i += 1
        if len(outputLayers) > 0:
            self.__addCtrlLayers(outputLayers, styleLayers)
            #print "Erreur totale : " + str(totalError)
            self.__iface.messageBar().clearWidgets()
            self.__iface.messageBar().pushMessage("Info", u"Toutes les couches ont été chargées avec succès dans le projet / Total des erreurs :" + str(totalError), level=QgsMessageBar.INFO, duration=10)
        else:
            #print "Erreur totale : " + str(totalError)
            self.__iface.messageBar().clearWidgets()
            self.__iface.messageBar().pushMessage("Info", u"Yes !! Aucune erreur a été détectée sur la zone définie ", level=QgsMessageBar.INFO, duration=5)

    def __addCtrlLayers(self, layers, styles):
        """
        Ajout des couches du résultats des requêtes de contrôles
        :param layers: Liste des couches à ajouter au projet
        :return:
        """

        groupName = 'CONTROL (' +datetime.now().strftime("%Y-%m-%d")+')' # définir le nom du groupe dans lequel seront ajouté chaque couche
        project_tree = QgsProject.instance().layerTreeRoot()             # arbre des couches
        if project_tree.findGroup(groupName) is None:
            #iface.legendInterface().addGroup( 'CONTROL')
            ctrl_group = project_tree.insertGroup(0,groupName)
        else:
            ctrl_group = project_tree.findGroup(groupName)
        ctrl_group.removeAllChildren()                                  # effacer les couches existantes prend du temps !!


        for i in range(0,len(layers)):
            '''
            layerStyle = QgsMapLayerStyle('//geodata.lausanne.ch/data/QGIS_projet/eauservice/qwat_lausanne/qml/control_layer/conduites_non_connectees.qml')
            layerStyle.writeToLayer(layers[i])
            layers[i].triggerRepaint()
            layerStyleManager = layers[i].styleManager()
            layerStyleManager.addStyle('control_style', layerStyle)
            layerStyleManager.setCurrentStyle('control_style')
            '''
            layers[i].loadNamedStyle(styles[i])
            QgsMapLayerRegistry.instance().addMapLayer(layers[i],False)
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
