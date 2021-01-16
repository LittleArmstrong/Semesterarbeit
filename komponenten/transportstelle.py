#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .upvia import Upvia
from ast import literal_eval

class Transportstelle(Upvia):
    # __init__ und exklusive Funktionen
    def __init__(self, vcscript):
        super(Transportstelle, self).__init__(self)
        # Konstanten
        self.TYP = 'Transportstelle'
        # Referenz zur Anwendung, der Komponente und dem Moduel
        self.App = vcscript.getApplication()
        self.Komponente = vcscript.getComponent()
        self.Vcscript = vcscript
        # Behaviours
        self.Container = self.Komponente.findBehaviour('ComponentContainer__HIDE__')
        # - PathInterface notwendig, sonst können keine Komponenten erkannt werden
        self.Interface = self.Komponente.findBehaviour('PathInterface')
        # - wird weiter unten bestimmt
        self.Path = None
        self.Sensor = self.Komponente.findBehaviour('ComponentPathSensor')
        # - Sensorsignale
        self.Komp_signal = self.Sensor.ComponentSignal
        self.Bool_signal = self.Sensor.BoolSignal
        # Eigenschaften
        # - Zu erstellende Komponenten, falls das Signal gegeben wird
        self.Produkte = self.Komponente.getProperty('Schnittstelle::Produkte')
        if self.Produkte:
            self.Produkte.OnChanged = self.ermittle_creators()
        self.Stop = self.Komponente.getProperty('Schnittstelle::Stop')
        # Erstelle Behaviours und Eigenschaften falls notwendig
        self.konfiguriere_komponente(vcscript)
        # Pfad des  Fließbandes, falls verbunden und zu erstellende Produkte bestimmen
        self.ermittle_path_produkte()
            
    def konfiguriere_komponente(self, vcscript):
        # Behaviours
        script = self.Komponente.findBehaviour('Script')
        if not self.Komponente.findBehaviour('UpdateSignal'):
            update = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
            update.Connections = [script]
        # Eigenschaften
        # - Ob Komponente gestoppt werden soll oder nicht
        if not self.Stop:
            self.Stop = self.Komponente.createProperty(vcscript.VC_BOOLEAN, 'Schnittstelle::Stop')
            self.Stop.Value = False
        # - Typ: Beschreibt die Funktion dieser Komponente und wie diese mit andere Komponenten interagiert
        typ = self.Komponente.getProperty('Schnittstelle::Typ')
        if not typ:
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP
        if not self.Produkte:
            self.Produkte = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Produkte')
            self.Produkte.OnChanged = self.ermittle_creators()
        # Boolsignal mit Container verbinden, damit wir wissen ob eine Komponente platziert wurde oder nicht
        self.Container.TransitionSignal = self.Bool_signal
        # Verbinde die Signale mit diesem Script
        self.check_verbindungen()

    def OnStart(self):
        # Eigenschaften der Klasse upvia initialisert/resettet
        self.reset_OnStart()
        # Ermittle Path und Wert für Produkte
        self.ermittle_path_produkte()
        # Objekt-Eigenschaften
        self.Anlage = self.App.findComponent('Schnittstelle').getProperty('Schnittstelle::Anlage').Value
        # - Variablen für die Position
        self.Path_distanz = self.Komponente.PositionMatrix.P.X
        self.Weltposition = self.Komponente.WorldPositionMatrix
        # Verbinde Signale mit diesem Script
        self.check_verbindungen()
        

    def OnSignal(self, signal):
         # Signale unterscheiden sich je nachdem, ob es sich um eine reale oder virtuelle Anlage handelt
        if self.Anlage == 'virtuell':
            # UpdateSignal ist ein Stringsignal. Gibt an, dass eine bestimmte Funktion ausgeführt werden soll. Enthält ggf. extra Info.
            if signal.Name == 'UpdateSignal':
                # Zu erfüllende Funktion ggf. mit extra Info
                update = literal_eval(signal.Value)
                if update['Funktion'] == 'signal':
                    # Erstelle Komponente, falls keine vorhanden und entferne nächste Komponente vor dem Sensor
                    self.vergleiche_virtuell(update['Info'])
            # KompSignal signalisert Komponenten auf dem Pfad/Sensor
            elif signal == self.Komp_signal:
                self.vergleiche_real()
        elif self.Anlage == 'real':
            if signal == self.Komp_signal and signal.Value:
                # Sende ein Signal an die virtuelle Anlage, dass ein Produkt hier ist
                self.update_db('signal', signal.Value.Name)

    def OnRun(self):
        while True:
            if self.Stop.Value:
                # Falls Komponente gestoppt werden soll, warte auf Signal und stoppe es
                self.Vcscript.triggerCondition(lambda: self.Vcscript.getTrigger() == self.Komp_signal and self.Komp_signal.Value)
                part = self.Komp_signal.Value
                part.stopMovement()
            else:
                # Gelangt eine Komponente ins Container so wird das BoolSignal positiv
                self.Vcscript.triggerCondition(lambda: self.Vcscript.getTrigger() == self.Bool_signal and self.Bool_signal.Value)
                if self.Container.Components:
                    part = self.Container.Components[0]
                    self.Path.grab(part)
    
    def check_verbindungen(self):
        script = self.Komponente.findBehaviour('Script')
        # Verbinde Komponentensignal mit diesem Script
        if script not in self.Komp_signal.Connections:
            self.Komp_signal.Connections += [script]
        # Verbinde BoolSignal mit diesem Script
        if script not in self.Bool_signal.Connections:
            self.Bool_signal.Connections += [script]
    
    def ermittle_path_produkte(self):
        komp = self.Interface.ConnectedComponent
        if not komp:
            return
        self.Path = komp.findBehavioursByType(self.Vcscript.VC_ONEWAYPATH)[0]
        produkte = komp.getProperty('Schnittstelle::Produkte')
        if not produkte:
            return
        self.Produkte.Value = produkte.Value

    
    
