#!/usr/bin/env python
# -*- coding: utf-8 -*-
class Transportstelle():
    # __init__ und exklusive Funktionen
    def __init__(self, vcscript):
        # Konstanten
        self.TYP = 'Transportstelle'
        # Referenz zur Anwendung, der Komponente und dem Moduel
        self.App = vcscript.getApplication()
        self.Komponente = vcscript.getComponent()
        self.Vcscript = vcscript
        # Behaviours
        self.Container = self.Komponente.findBehaviour('ComponentContainer__HIDE__')
        # - Interface notwendig, sonst funktioniert Kompsignal nicht
        self.Interface = self.Komponente.findBehaviour('PathInterface')
        self.Sensor = self.Komponente.findBehaviour('ComponentPathSensor')
        # - Sensorsignale
        self.Komp_signal = self.Sensor.ComponentSignal
        self.Bool_signal = self.Sensor.BoolSignal
        # Eigenschaften
        self.Stop = self.Komponente.getProperty('Schnittstelle::Stop')
        # Pfad des verbundenen Fließbandes
        self.Path = self.Interface.ConnectedComponent.findBehavioursByType(vcscript.VC_ONEWAYPATH)[0]
    
    def konfiguriere_komponente(self, vcscript):
        # Referenz zum Script
        script = self.Komponente.findBehaviour('Script')
        # Eigenschaften
        # - Ob Komponente gestoppt werden soll oder nicht
        if not self.Stop:
            self.Stop = self.Komponente.createProperty(vcscript.VC_BOOLEAN, 'Schnittstelle::Stop')
        # Verbinde Komponentensignal mit diesem Script
        if script not in self.Komp_signal.Connections:
            self.Komp_signal.Connections += [script]
        # Verbinde BoolSignal mit diesem Script
        if script not in self.Bool_signal.Connections:
            self.Bool_signal.Connections += [script]

    def OnStart(self):
        pass

    def OnSignal(self, signal):
        pass

    def OnRun(self):
        while True:
            if self.Stop.Value:
                # Falls Komponente gestoppt werden soll, warte auf Signal und stoppe es
                self.Vcscript.triggerCondition(lambda: self.Vcscript.getTrigger() == self.Komp_signal and self.Komp_signal.Value)
                part = self.Komp_signal.Value
                part.stopMovement()
            else:
                # Ansonsten warte auf ein positives BoolSignal und leite die Komponente weiter zum Pfad
                # Wird eine Komponente durch ein Roboter platziert, so wird diese nicht durch das KompSignal erfasst, deswegen BoolSignal
                self.Vcscript.triggerCondition(lambda: self.Vcscript.getTrigger() == self.Bool_signal and self.Bool_signal.Value)
                if self.Container.Components:
                    part = self.Container.Components[0]
                    self.Path.grab(part)