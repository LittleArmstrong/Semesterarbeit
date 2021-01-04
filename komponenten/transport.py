#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .datenbank import Datenbank
from ast import literal_eval
import konstanten

class Transport():
    def __init__(self, vcscript):
        # Konstanten
        self.DATENBANK_PFAD = konstanten.PFAD_SIGNALE_VIRTUELL
        self.DATENBANK_TABELLE = konstanten.TABELLE_SIGNALE
        self.TYP = 'Transport'

        # Referenz zur Anwendung selbst
        self.App = vcscript.getApplication()

        # Referenz zur Komponente
        self.Komponente = vcscript.getComponent()

        # Komponenten-Eigenschaften
        self.Name = self.Komponente.Name
        self.Position = self.Komponente.PositionMatrix

        # Behaviours der Komponente
        self.Komponente_signal = self.Komponente.findBehaviour('SensorSignal') or self.Komponente.findBehaviour('ComponentSignal')
        self.Update_signal = self.Komponente.findBehaviour('UpdateSignal')
        self.Creator = self.Komponente.findBehaviour('ComponentCreator')
        self.Container = self.Komponente.findBehaviour('ComponentContainer')
        self.Path = self.Komponente.findBehaviour('One-WayPath__HIDE__') or self.Komponente.findBehaviour('Path__HIDE__')
        self.Interface_in = self.Komponente.findBehaviour('InInterface')
        self.Interface_out = self.Komponente.findBehaviour('OutInterface')
        self.Sensor = self.Komponente.findBehaviour('ComponentPathSensor')

        # Eigenschaften der Komponente
        self.Produkt = self.Komponente.getProperty('Schnittstelle::Produkt')
    
        # Erstelle Behaviours, Eigenschaften und Verbindungen, wenn notwendig
        self.konfiguriere_komponente(vcscript)

        # Objekt-Eigenschaften
        self.Anlage = None
        self.Zuletzt_erstellte_komponente = 0
        self.Aktuelle_Komponente = None
        self.Path_position_anfang = self.Path.Path[0].FramePositionMatrix.P
        self.Sensor_position = self.Sensor.Frame.FramePositionMatrix.P
        self.Sensor_position_welt = self.Position * self.Sensor.Frame.FramePositionMatrix
        self.Sensor_path_distanz = (self.Sensor_position - self.Path_position_anfang).length()
        self.Vorheriges_produkt = self.Produkt.Value
        self.Umleiten_zu = None
        self.Umleiten_zu_Position = None
        self.Umleiten_zu_Path = None

        # Referenz zu anderen Komponenten, Behaviours oder Eigenschaften
        self.Komponente_schnittstelle_anlage = self.App.findComponent('Schnittstelle').getProperty('Schnittstelle::Anlage')

        # Wertzuweisungen
        self.Creator.getProperty('Interval').Value = 0
        self.Creator.getProperty('Limit').Value = 0
        self.Path.getProperty('RetainOffset').Value = False
        self.Komponente.getProperty('Schnittstelle::Typ').Value = self.TYP

        

    def OnStart(self):
        # Reset Signale
        self.Signal_real = 0
        self.Signal_virtuell = 0
        self.Umleiten_zu = None
        self.Umleiten_zu_Path = None
        self.Umleiten_zu_Position = None

        # Lege fest, ob virtuelle oder reale Anlage, falls nicht schon festgelegt
        if self.Anlage != self.Komponente_schnittstelle_anlage.Value and not self.Anlage:
            self.Anlage = self.Komponente_schnittstelle_anlage.Value 
        
        # Beim gebogenem Rollband wird die Sensorposition aus irgendeinem Grund resettet, deswegen wird er hier neu zugewiesen
        if not self.Sensor.Frame:
            frame = self.Komponente.findFeature('frame_2') or self.Komponente.findFeature('Mid')
            self.Sensor.Frame = frame
        
        # Lege Produkt für alle verbundene Komponenten fest
        if self.Vorheriges_produkt != self.Produkt.Value:
            self.Vorheriges_produkt = self.Produkt.Value
            self.set_part(self.Produkt, self.Creator)
            self.update_eigenschaft_verbundener_komponenten(self.Produkt, 'InInterface')
            self.update_eigenschaft_verbundener_komponenten(self.Produkt, 'OutInterface')

    def OnSignal(self, signal):
        if signal == self.Update_signal:
            update = literal_eval(signal.Value)
            if update['Funktion'] == 'signal' and update['Info']:
                self.Signal_real = update['Info']
            elif update['Funktion'] == 'umleiten':
                if not self.Umleiten_zu or self.Umleiten_zu != update['Info']:
                    self.Umleiten_zu = update['Info']
                elif self.Umleiten_zu == update['Info']:
                    self.Umleiten_zu = None
                    self.Umleiten_zu_Position = None
                    self.Umleiten_zu_Path = None

        if signal == self.Komponente_signal:
            if self.Anlage == 'real':
                if signal.Value:
                    if self.Umleiten_zu:
                        self.umleiten(komponente = signal.Value)
                    else:
                        self.update_datenbank_virtuell('signal', '1')
            elif self.Anlage == 'virtuell':
                if signal.Value:
                    self.Signal_virtuell = 1
                    self.Aktuelle_Komponente = signal.Value
                else:
                    self.Signal_virtuell = 0
                    self.Aktuelle_Komponente = None

        if self.Aktuelle_Komponente != self.Zuletzt_erstellte_komponente and self.Anlage == 'virtuell':
            if self.Signal_virtuell and not self.Signal_real:
                self.Aktuelle_Komponente.delete()
                self.Signal_virtuell = 0
            elif not self.Signal_virtuell and self.Signal_real:
                self.entferne_erste_komponente_vor_sensor()
                self.Zuletzt_erstellte_komponente = self.erstelle_komponente_am_sensor()
                self.Signal_real = 0

    def OnRun(self):
        pass

    def konfiguriere_komponente(self, vcscript):
        # Referenz zum Pythonscript
        script = self.Komponente.findBehaviour('PythonScript')

        # Behaviours
        if not self.Creator:
            self.Creator = self.Komponente.createBehaviour(vcscript.VC_COMPONENTCREATOR, 'ComponentCreator')

        if not self.Container:
            self.Container = self.Komponente.createBehaviour(vcscript.VC_COMPONENTCONTAINER, 'ComponentContainer')
            # Verbinde Container mit Creator
            container_input = self.Container.getConnector('Input')
            creator_output = self.Creator.getConnector('Output')
            container_input.connect(creator_output)
            
        if not self.Update_signal:
            self.Update_signal = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
            self.Update_signal.Connections = [script]
        
        if not self.Komponente_signal:
            self.Komponente_signal = self.Komponente.createBehaviour(vcscript.VC_COMPONENTSIGNAL, 'SensorSignal')
            self.Komponente_signal.Connections = [script]
            self.Sensor.ComponentSignal = self.Komponente_signal

        # Eigenschaften
        if not self.Produkt:
            self.Produkt = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Produkt')

        # Eigenschaften ohne Referenz, nur zur Wertzuweisung
        if not self.Komponente.getProperty('Schnittstelle::Typ'):
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP
            
        # Verbindungen zwischen Behaviours
        verbindungen = self.Komponente_signal.Connections
        if not script in verbindungen:
            verbindungen += [script]
            self.Komponente_signal.Connections = verbindungen

        if not self.Sensor.Frame:
            frame = self.Komponente.findFeature('Mid') or self.Komponente.findFeature('frame_2')
            self.Sensor.Frame = frame

    def erstelle_komponente_am_sensor(self):
        erstellte_komponente = self.Creator.create()
        erstellte_komponente.PositionMatrix = self.Sensor_position_welt
        self.Path.grab(erstellte_komponente)
        return erstellte_komponente

    def entferne_erste_komponente_vor_sensor(self):
        komponenten = self.Path.Components
        if komponenten:
            komponenten_path_distanz = [(komponente.PositionMatrix.P - self.Path_position_anfang).length() for komponente in komponenten]
            komponenten_sensor_distanz = [self.Sensor_path_distanz - komponente for komponente in komponenten_path_distanz]
            komponenten_distanz_vor_sensor = [distanz for distanz in komponenten_sensor_distanz if distanz > 0]
            if komponenten_distanz_vor_sensor:
                index_erste_komponente_vor_sensor = komponenten_sensor_distanz.index(min(komponenten_distanz_vor_sensor))
                komponente_vor_sensor = komponenten[index_erste_komponente_vor_sensor]
                komponente_vor_sensor.delete()

    def update_datenbank_virtuell(self, funktion, wert):
        db = Datenbank(self.DATENBANK_PFAD)
        parameter = (self.Name, self.TYP, 'signal', '1')
        db.replace_query(self.DATENBANK_TABELLE, parameter)

    def set_part(self, produkt, creator):
        if produkt.Value != creator.Part:
            produkt = self.App.findComponent(produkt.Value)
            uri = produkt.Uri
            creator.Part = uri

    def update_eigenschaft_verbundener_komponenten(self, eigenschaft, interface):
        komponente = self.Komponente.findBehaviour(interface).ConnectedComponent
        eigenschaft_name = eigenschaft.Name
        eigenschaft_wert = eigenschaft.Value
        while komponente:
            eigenschaft = komponente.getProperty(eigenschaft_name)
            if eigenschaft and eigenschaft.Value != eigenschaft_wert:
                eigenschaft.Value = eigenschaft_wert
            else:
                break
            komponente = komponente.findBehaviour(interface).ConnectedComponent
    
    def umleiten(self, komponente):
        komponente.delete()
        if not self.Umleiten_zu_Path or not self.Umleiten_zu_Position:
            ziel_komponente = self.App.findComponent(self.Umleiten_zu)
            ziel_komponente_sensor = ziel_komponente.findBehaviour('ComponentPathSensor')
            self.Umleiten_zu_Position = ziel_komponente.PositionMatrix * ziel_komponente_sensor.Frame.FramePositionMatrix
            self.Umleiten_zu_Path = ziel_komponente.findBehaviour('One-WayPath__HIDE__') or ziel_komponente.findBehaviour('Path__HIDE__')

        erstellte_komponente = self.Creator.create()
        erstellte_komponente.PositionMatrix = self.Umleiten_zu_Position
        self.Umleiten_zu_Path.grab(erstellte_komponente)

        

    
            
        
        



        
        
