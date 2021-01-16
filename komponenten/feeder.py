#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ast import literal_eval

class Feeder():
    def __init__(self, vcscript):
        # Konstanten
        self.TYP = 'Feeder'
        # Referenz zur Anwendung, der Komponente und dem Modul 
        self.App = vcscript.getApplication()
        self.Komponente = vcscript.getComponent()
        self.Vcscript = vcscript
        # Behaviours der Komponente
        self.Creator = self.Komponente.findBehaviour('ComponentCreator__HIDE__')
        self.Update_signal = self.Komponente.findBehaviour('UpdateSignal')
        # Eigenschaften der Komponente
        self.Produkt = self.Komponente.getProperty('Schnittstelle::Produkt')
        # Erstelle die Eigenschaften und Behaviours, falls diese nicht existieren
        self.konfiguriere_komponente(vcscript)
        # Importierte Funktionen
        self.suspend = vcscript.suspendRun
        self.resume = vcscript.resumeRun
        self.delay = vcscript.delay

    def konfiguriere_komponente(self, vcscript):
        # Referenz zum PythonScript
        script = self.Komponente.findBehaviour('Script')
        # Behaviours
        # - Creator: Zum erstellen von Komps
        if not self.Creator:
            self.Creator = self.Komponente.createBehaviour(vcscript.VC_COMPONENTCREATOR, 'ComponentCreator__HIDE__')
        # - Container: Temporäre Aufbewahrung, um Position festlegen zu können
        container = self.Komponente.findBehaviour('ComponentContainer__HIDE__')
        if not container:
            container = self.Komponente.createBehaviour(vcscript.VC_COMPONENTCONTAINER, 'ComponentContainer__HIDE__')
        # - UpdateSignal: Zum erhalten von Info und Befehlen
        update_signal = self.Komponente.findBehaviour('UpdateSignal')
        if not update_signal:
            update_signal = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
        # Eigenschaften
        if not self.Komponente.getProperty('Schnittstelle::Typ'):
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP
        # - Produkt: Bestimmt welches Produkt hergestellt werden soll (Name). Produkt muss innerhalb Layout irgendwo platziert sein
        if not self.Produkt:
            self.Produkt = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Produkt')
        # Verbindungen zwischen Behaviours
        # - Verbinde UpdateSignal mit Script
        if [script] not in update_signal.Connections:
            update_signal.Connections = [script]
        # - Verbinde Creator-Output mit Container-Input
        creator_output = self.Creator.getConnector('Output')
        if not creator_output.Connection:
            creator_output.connect(container.getConnector('Input'))

    def OnStart(self):
        frame_pos = self.Komponente.findFeature('MainFrame').FramePositionMatrix
        komp_pos = self.Komponente.WorldPositionMatrix
        welt_pos = komp_pos * frame_pos
        # Objekt-Eigenschaften
        self.Intervall = 0
        self.Position = welt_pos
        self.Update_produkt = None
        # - Path des Fließbandes
        self.Path = self.Komponente.findBehaviour('ConveyorInterface').ConnectedComponent.findBehavioursByType(self.Vcscript.VC_ONEWAYPATH)[0]
        # Reset Creator, damit keine Komponenten erstellt werden
        self.Creator.Interval = 0
        self.Creator.Limit = 0
        # Lege die zu erstellende Komponente fest
        self.Creator.Part = self.App.findComponent(self.Produkt.Value).Uri

    def OnSignal(self, signal):
        # Lege Intervall fest und erstelle Komponente, falls direkt eine erstellt werden soll
        if signal.Name == 'UpdateSignal':
            update = literal_eval(signal.Value)
            if update['Funktion'] == 'erstelle':
                self.erstelle_komponente()
            elif update['Funktion'] == 'intervall':
                self.set_intervall(int(update['Info']), False)
            elif update['Funktion'] == 'intervall_sofort':
                self.set_intervall(int(update['Info']), True)
            
    def set_intervall(self, intervall, sofort = False):
        # Lege intervall fest
        if intervall:
            if sofort:
                self.erstelle_komponente()
            self.Intervall = intervall
            self.resume()
        else:
            self.suspend()

    def OnRun(self):
        # Erstelle Komponente abh. vom festgelegten Intervall
        while True:
            if not self.Intervall:
                self.suspend()
            elif self.Intervall:
                # Erstelle und positioniere Komponente
                self.erstelle_komponente()
            self.delay(self.Intervall)
    
    def erstelle_komponente(self):
        # Erstelle Komponente, lege Position fest und platziere auf Path
        komp = self.Creator.create()
        komp.PositionMatrix = self.Position
        self.Path.grab(komp)
            
    
    
    

    


    