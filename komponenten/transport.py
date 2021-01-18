#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .datenbank import Datenbank
from .upvia import Upvia
from ast import literal_eval
import konstanten

class Transport(Upvia):
    # __init__ und exklusive Funktionen
    def __init__(self, vcscript):
        # Funktionen und Eigenschaften der Oberklasse
        super(Transport, self).__init__()
        # Konstanten
        self.TYP = 'Transport'
        # Referenz zur Anwendung, Komponente und dem Modul 
        self.App = vcscript.getApplication()
        self.Komponente = vcscript.getComponent()
        self.Vcscript = vcscript
        
        # Behaviours der Komponente
        self.Container = self.Komponente.findBehaviour('ComponentContainer__HIDE__')
        # - Der erste gefundene Pfad wird gewählt, deshalb sollte der gewünschte Pfad and erster Stelle stehen
        # - oder nach einem bestimmten Pfad gesucht werden
        self.Path = self.Komponente.findBehavioursByType(vcscript.VC_ONEWAYPATH)[0]
        # Behaviours abh. vom Pfad
        # - Der erste gefunde Sensor auf dem Pfad wird gewählt -> Sollte ein ComponentPathSensor sein!
        if self.Path.Sensors:
            self.Sensor = self.Path.Sensors[0]
            # Behaviour abh. vom Sensor
            self.Komp_signal =  self.Sensor.ComponentSignal
        else:
            self.Sensor = None
            self.Komp_signal = None
        # Erstelle Behaviours, Eigenschaften und Verbindungen, falls notwendig
        self.konfiguriere_komponente(vcscript)
        # Importierte Funktionen
        self.resume = vcscript.resumeRun
        self.suspend = vcscript.suspendRun
        
    def konfiguriere_komponente(self, vcscript):
        # Referenz zum Pythonscript
        script = self.Komponente.findBehaviour('Script')
        # Behaviours
        # - ComponentContainer, zur temporären Aufbewahrung der Produkte, damit denen eine Position auf dem Pfad zugewiesen werden kann
        if not self.Container:
            self.Container = self.Komponente.createBehaviour(vcscript.VC_COMPONENTCONTAINER, 'ComponentContainer__HIDE__')
        # - Sensor: existiert keins, dann wird eins erstellt und dem Pfad zugewiesen
        if not self.Sensor:
            sensor = self.Komponente.findBehaviour('ComponentPathSensor')
            if not sensor:
                self.Sensor = self.Komponente.createBehaviour(vcscript.VC_COMPONENTPATHSENSOR, 'ComponentPathSensor')
            else:
                self.Sensor = sensor
            self.Path.Sensors = [self.Sensor]
        # -- Sensorposition (Pfadmitte) festlegen, falls nicht gegeben
        self.set_sensor_frame()
        # - Komponentensignal: zum signalisieren von Komponenten durch Sensor
        if not self.Komp_signal:
            komp_signal = self.Komponente.findBehaviour('ComponentSignal')
            if not komp_signal:
                self.Komp_signal = self.Komponente.createBehaviour(vcscript.VC_COMPONENTSIGNAL, 'ComponentSignal')
            else:
                self.Komp_signal = komp_signal
            self.Sensor.ComponentSignal = self.Komp_signal
        # -- Verbinde Komponentensignal mit diesem Script
        if script not in self.Komp_signal.Connections:
            self.Komp_signal.Connections += [script]
        # - UpdateSignal + Verbindung zum Script
        if not self.Komponente.findBehaviour('UpdateSignal'):
            update = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
            update.Connections = [script]
        # Eigenschaften
        # - Typ
        if not self.Komponente.getProperty('Schnittstelle::Typ'):
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP

    # OnStart-Event
    def OnStart(self):
        # Beim Kurven-Rollband wird die Sensorposition aus irgendeinem Grund resettet, deswegen wird er hier neu zugewiesen
        # ! Kurven-Rollband nicht kopieren, sondern einzeln in das Layout platzieren, da sonst die frames sich beim Pfad
        # aus irgendeinem Grund ändern !
        self.set_sensor_frame()
        # Objekt-Eigenschaften
        # - Methode der Oberklasse
        self.reset_OnStart(self.App)
        self.Anlage = self.App.findComponent('Schnittstelle').getProperty('Schnittstelle::Anlage').Value
        # - Position und distanz des Sensors. Name wichtig, wird von der Klasse Upvia benutzt
        self.Path_distanz = self.Sensor.Frame.FramePositionMatrix.P.X 
        self.Weltposition = self.Komponente.PositionMatrix * self.Sensor.Frame.FramePositionMatrix
        self.Umleiten = None
    
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
                    self.vergleiche_virtuell(update['Info'], self.Path, self.Path_distanz, self.Weltposition)
            # KompSignal signalisert Komponenten auf dem Pfad/Sensor
            elif signal == self.Komp_signal:
                self.vergleiche_real(signal)
        elif self.Anlage == 'real':
            if signal.Name == 'UpdateSignal':
                update = literal_eval(signal.Value)
                if update['Funktion'] == 'umleiten':
                    # Untersucht, ob umgeleitet werden soll und wohin und speichert die Info
                    self.update_umleite(update['Info'])
                elif update['Funktion'] == 'erstelle':
                    # Erstellt Komponente
                    self.Produktname = update['Info']
                    self.erstelle_komponente(self.Path, self.Weltposition)
            elif signal == self.Komp_signal and signal.Value:
                # Falls umgeleitet werden soll, entferne Komp und erstelle neue am jeweiligen Fließband
                if self.Umleiten:
                    self.umleite_komp(signal.Value)
                # Wenn nicht, dann sende ein Signal an die virtuelle Anlage, dass ein Produkt hier ist
                else:
                    self.update_db(self.Komponente.Name, self.TYP, 'signal', signal.Value.Name)

    def umleite_komp(self, komp):
        # Sende ein Signal zum Fließband, zu der umgeleitet werden. Erstelle dort Komponente und entferne hier Komponente
        info = repr({'Funktion':'erstelle', 'Info': komp.Name})
        self.Umleiten.signal(info)
        komp.delete()

    def update_umleite(self, zu_komp):
        # Lege fest ob umgeleitet werden soll oder nicht und wohin und speichere die Info
        update = self.App.findComponent(zu_komp).findBehaviour('UpdateSignal')
        if update != self.Umleiten:
            self.Umleiten = update
        else:
            self.Umleiten = None

    def OnRun(self):
        pass

    # Funktionen die in mehr als einem Event auftreten
    def set_sensor_frame(self):
        if not self.Sensor.Frame:
            index_frame = int(len(self.Path.Path)/2)
            frame = self.Path.Path[index_frame]
            self.Sensor.Frame = frame

        


        

    
            
        
        



        
        
