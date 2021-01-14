#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .datenbank import Datenbank
from ast import literal_eval
import konstanten

class Transport():
    # __init__ und exklusive Funktionen
    def __init__(self, vcscript):
        # Konstanten
        self.DB_PFAD = konstanten.PFAD_SIGNALE_VIRTUELL
        self.DB_TABELLE = konstanten.TABELLE_SIGNALE
        self.TYP = 'Transport'
        # Referenz zur Anwendung selbst
        self.App = vcscript.getApplication()
        # Referenz zur Komponente
        self.Komponente = vcscript.getComponent()
        # Behaviours der Komponente
        self.Creator = self.Komponente.findBehaviour('ComponentCreator')
        # - Der erste gefundene Pfad wird gewählt, deshalb sollte der gewünschte Pfad and erster Stelle stehen
        # - oder nach einem bestimmten Pfad gesucht werden
        self.Path = self.Komponente.findBehavioursByType(vcscript.VC_ONEWAYPATH)[0]
        # Behaviours abh. vom Pfad
        # - Der erste gefunde Sensor auf dem Pfad wird gewählt -> Sollte ein ComponentPathSensor sein!
        self.Sensor = self.Path.Sensors[0]
        # Behaviour abh. vom Sensor
        self.Komp_signal =  self.Sensor.ComponentSignal
        # Erstelle Behaviours, Eigenschaften und Verbindungen, falls notwendig
        self.konfiguriere_komponente(vcscript)
        
    def konfiguriere_komponente(self, vcscript):    
        # Referenz zum Pythonscript
        script = self.Komponente.findBehaviour('Script')
        # Behaviours
        # - ComponentCreator, zum erstellen von Produkten (Für virtuelle Anlage oder Umleiten wichtig)
        if not self.Creator:
            self.Creator = self.Komponente.createBehaviour(vcscript.VC_COMPONENTCREATOR, 'ComponentCreator')
        # - ComponentContainer, zur temporären Aufbewahrung der Produkte, damit denen eine Position auf dem Pfad zugewiesen werden kann
        if not self.Komponente.findBehaviour('ComponentContainer'):
            container = self.Komponente.createBehaviour(vcscript.VC_COMPONENTCONTAINER, 'ComponentContainer')
            # Verbinde Creator-Output mit Container-Input, damit die erstellten Produkte direkt im Container landen
            self.Creator.getConnector('Output').connect(container.getConnector('Input'))
        # - Sensor: existiert keins, dann wird eins erstellt und dem Pfad zugewiesen
        if not self.Sensor:
            self.Sensor = self.Komponente.createBehaviour(vcscript.VC_COMPONENTPATHSENSOR, 'ComponentPathSensor')
            self.Path.Sensors[0] = self.Sensor
        # -- Sensorposition (Pfadmitte) festlegen, falls nicht gegeben
        if not self.Sensor.Frame:
            index_frame = int(len(self.Path.Path)/2)
            frame = self.Path.Path[index_frame]
            self.Sensor.Frame = frame
        # - Komponentensignal: zum signalisieren von Komponenten durch Sensor
        if not self.Komp_signal:
            self.Komp_signal = self.Komponente.createBehaviour(vcscript.VC_COMPONENTSIGNAL, 'ComponentSignal')
            self.Sensor.ComponentSignal = self.Komp_signal
        # -- Verbinde Komponentensignal mit diesem Script
        if script not in self.Komp_signal.Connections:
            self.Komp_signal.Connections += [script]
        # - UpdateSignal + Verbindung zum Script
        if not self.Komponente.findBehaviour('UpdateSignal'):
            update = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'Update')
            update.Connections = [script]
        # Eigenschaften
        # - Typ
        if not self.Komponente.getProperty('Schnittstelle::Typ'):
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP

    # OnStart-Event
    def OnStart(self):
        # Variablen zur Bestimmung der Sensorposition
        path_anfang = self.Path.Path[0].FramePositionMatrix.P
        sensor_position = self.Sensor.Frame.FramePositionMatrix.P
        komp_position = self.Komponente.PositionMatrix
        # Objekt-Eigenschaften
        self.Anlage = self.App.findComponent('Schnittstelle').getProperty('Schnittstelle::Anlage').Value
        self.Erstellte_komp = None
        self.Sensor_path_distanz = (sensor_position - path_anfang).length()
        self.Sensor_weltposition = komp_position * sensor_position
        self.Uri = None 
        self.Umleiten = None
        # Reset ComponentCreator, damit keine Produkte von selbst hergestellt werden
        self.Creator.Interval = 0
        self.Creator.Limit = 0
        # Beim gebogenem Rollband wird die Sensorposition aus irgendeinem Grund resettet, deswegen wird er hier neu zugewiesen
        # if not self.Sensor.Frame:
            # index_frame = int(len(self.Path.Path)/2)
            # frame = self.Path.Path[index_frame]
            # self.Sensor.Frame = frame

    # OnSignal-Event und exklusive Funktionen
    def OnSignal(self, signal):
        # Signale unterscheiden sich je nachdem, ob es sich um eine reale oder virtuelle Anlage handelt
        if self.Anlage == 'virtuell':
            # UpdateSignal ist ein Stringsignal. Gibt an, dass eine bestimmte Funktion ausgeführt werden soll. Enthält ggf. extra Info.
            if signal.Name == 'UpdateSignal':
                # Zu erfüllende Funktion ggf. mit extra Info
                update = literal_eval(signal.Value)
                if update['Funktion'] == 'signal':
                    # Erstelle Komponente, falls keine vorhanden und entferne nächste Komponente vor dem Sensor
                    self.vergleiche_real(update['Info'])
            # KompSignal signalisert Komponenten auf dem Pfad/Sensor
            elif signal.Name == 'ComponentSignal' and signal.Value:
                # Entferne Komponente, falls nicht selbst erstellt
                if signal.Value != self.Erstellte_komp:
                    signal.Value.delete()
        elif self.Anlage == 'real':
            if signal.Name == 'UpdateSignal':
                update = literal_eval(signal.Value)
                if update['Funktion'] == 'umleiten':
                    # Untersucht, ob umgeleitet werden soll und wohin und speichert die Info
                    self.update_umleite(update['Info'])
                elif update['Funktion'] == 'erstelle':
                    # Erstellt Komponente
                    self.erstelle_komponente()
            elif signal.Name == 'ComponentSignal' and signal.Value:
                # Falls umgeleitet werden soll, entferne Komp und erstelle neue am jeweiligen Fließband
                if self.Umleiten:
                    self.umleite_komp(signal.Value)
                # Wenn nicht, dann sende ein Signal an die virtuelle Anlage, dass ein Produkt hier ist
                else:
                    self.update_db('signal', signal.Value.Uri)

    def entferne_komponente(self):
        # Entferne nächste Komponente vor Sensor, falls existiert
        komps = self.Path.Components
        if not komps:
            return
        komps_distanz = [self.Sensor_path_distanz - komp.getPathDistance() for komp in komps]
        pos_distanz = [dist for dist in komps_distanz if dist>0]
        index = komps_distanz.index(min(pos_distanz))
        komp = komps[index]
        if not komp:
            return
        komp.delete()

    def erstelle_komponente(self):
        # Erstelle Komponente am Sensor
        komp = self.Creator.create()
        komp.PositionMatrix = self.Sensor_weltposition
        self.Path.grab(komp)
        return komp

    def umleite_komp(self, komp):
        # Sende ein Signal zum Fließband, zu der umgeleitet werden. Erstelle dort Komponente und entferne hier Komponente
        info = repr({'Funktion':'erstelle', 'Info:': komp.Uri})
        self.Umleiten.signal(info)
        komp.delete()
    
    def update_db(self, funktion, wert):
        # Aktualisiere die Datenbank. Signale gelangen so zur virtuellen Anlage.
        db = Datenbank(self.DB_PFAD)
        parameter = (self.Komponente.Name, self.TYP, funktion, wert)
        db.replace_query(self.DB_TABELLE, parameter)
    
    def update_umleite(self, zu_komp):
        # Lege fest ob umgeleitet werden soll oder nicht und wohin und speichere die Info
        update = self.App.findComponent(zu_komp).findBehaviour('Update')
        if update != self.Umleiten:
            self.Umleiten = update
        else:
            self.Umleiten = None
        
    def vergleiche_real(self, uri):
        # Erhalte Uri des Produkts aus der realen Anlage, damit dieser in der virtuellen Anlage hergestellt werden kann
        if self.Uri != uri:
            self.Uri = uri
            self.Creator.Part = self.Uri
        # Erstelle Produkt, falls bei der virtuellen Anlage der Sensor nicht aktiviert wurde und entferne nächste Komp zum Sensor
        if not self.Komp_signal.Value:
            self.entferne_komponente()
            self.Erstellte_komponente = self.erstelle_komponente()
    
    def OnRun(self):
        pass

    







        

    
            
        
        



        
        
