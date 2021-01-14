#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .datenbank import Datenbank
from ast import literal_eval
import konstanten

class Maschine():
    # __init__ und exklusive Funktionen
    def __init__(self, vcscript):
        # Konstanten
        self.TYP = 'Maschine'
        # Referenz zur Anwendung und Komponente
        self.App = vcscript.getApplication()
        self.Komponente = vcscript.getComponent()
        # Behaviours der Komponente
        self.Auf = self.Komponente.findBehaviour('FROM_PLC_OpenDoor')
        self.Belegt = self.Komponente.findBehaviour('TransSignal')
        self.Container = self.Komponente.findBehavioursByType(vcscript.VC_COMPONENTCONTAINER)[0]
        self.Creator = self.Komponente.findBehaviour('ComponentCreator')
        self.istArbeiten = self.Komponente.findBehaviour('TO_PLC_ProcessIsRunning')
        self.istAuf = self.Komponente.findBehaviour('TO_PLC_DoorIsOpen')
        self.istZu = self.Komponente.findBehaviour('TO_PLC_DoorIsClosed')
        self.Start = self.Komponente.findBehaviour('FROM_PLC_StartProcess') 
        self.Zu = self.Komponente.findBehaviour('FROM_PLC_CloseDoor')
        # Eigenschaften der Komponente
        self.Anfangsprodukt = self.Komponente.getProperty('Schnittstelle::Anfangsprodukt')
        self.Endprodukt = self.Komponente.getProperty('Schnittstelle::Endprodukt')
        self.Prozesszeit = self.Komponente.getProperty('ProcessTime')
        # Erstelle Behaviours oder Eigenschaften falls notwendig
        self.konfiguriere_komponente(vcscript)
        # Importierte Funktionen
        self.resume = vcscript.resumeRun    
        self.suspend = vcscript.suspendRun

    def konfiguriere_komponente(self, vcscript):
        # Referenz zum Pythonscript selbst
        script = self.Komponente.findBehaviour('Script')
        # Behaviours
        # - UpdateSignal, um Befehle erhalten zu können
        if not self.Komponente.findBehaviour('UpdateSignal'):
            self.Update_signal = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
            self.Update_signal.Connections = [script]
        # - ComponentCreator, um Endprodukt zu erstellen
        if not self.Creator:
            self.Creator = self.Komponente.createBehaviour(vcscript.VC_COMPONENTCREATOR, 'ComponentCreator')
            self.Creator.getConnector('Output').connect(self.Container.getConnector('Input'))
        # Eigenschaften
        # - Falls Anfangsprodukt in Maschine, dann soll am Ende des Prozesses dieses in Endprodukt umgewandelt werden
        # - Name des Produktes angeben und Produkt irgendwo in Simulation platzieren
        if not self.Anfangsprodukt:
            self.Anfangsprodukt = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Anfangsprodukt')
        if not self.Endprodukt:
            self.Endprodukt = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Endprodukt')
        # - Typ, um Komponente und dessen Funktion zu erkennen
        if not self.Komponente.getProperty('Schnittstelle::Typ'):
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP

    # OnStart-Event
    def OnStart(self):
        # Objekt-Eigenschaften
        self.Fertig = False
        self.Steuerung = 'automatisch'
        # - Uri ist notwendig für den ComponentCreator, um das Endprodukt herzustellen
        self.Uri = self.App.findComponent(self.Endprodukt.Value).Uri
        # Reset Werte
        # - Damit Roboter weiß, dass die Türen offen sind
        self.istAuf.signal(True)
        # - Damit keine Produkt von selbst hergestellt werden
        self.Creator.Interval = 0
        self.Creator.Limit = 0
        # - Gibt dem Creator die notwendige Information, um das gewünsche Produkt zu erstellen
        self.Creator.Part = self.Uri

    # OnSignal-Event und exklusive Funktionen
    def OnSignal(self, signal):
        # UpdateSignal ist ein Stringsignal. Gibt an, dass eine bestimmte Funktion aktiviert werden soll. Enthält ggf. extra Info.
        if signal.Name == 'UpdateSignal':
            update = literal_eval(signal.Value) 
            # Schalte um zwischen Automatik und Manuell
            if update['Funktion'] == 'auto':
                self.switch_auto()
            else:
                self.Steuerung = 'manuell'
            # Stelle die Prozesszeit ein
            if update['Funktion'] == 'zeit':
                self.update_prozesszeit(update['Info'])
            # Öffne die Türen
            if update['Funktion'] == 'auf':
                self.Auf.signal(True)
            # Schließe die Türen
            elif update['Funktion'] == 'zu':
                self.Zu.signal(True)
            # Starte den Prozess. Funktioniert nur mit geschlossenen Türen.
            elif update['Funktion'] == 'start':
                self.Start.signal(True)
        # BoolSignal, dass angibt, ob eine Komponente platziert wurde oder nicht
        elif signal == self.Belegt:
            # Belegt und nicht gleich Endzustand, dann starte Prozess
            if signal.Value and self.Container.Components[0].Name != self.Endprodukt.Value:
                self.resume()
            # Belegt, aber gleich Endprodukt, dann ist Prozess fertig
            elif signal.Value and self.Container.Components[0].Name == self.Endprodukt.Value:
                self.Fertig = True
            # Sonst nicht fertig
            else:
                self.Fertig = False
        # Prozesssignal: aktiviert, am Anfang und Ende
        elif signal == self.istArbeiten:
            # Prozess zu Ende: Falls Komponente gleich Anfangszustand, dann wandle um in Endzustand
            if not self.istArbeiten.Value:
                if self.Container.Components and self.Container.Components[0].Name == self.Anfangsprodukt.Value:
                    self.Container.Components[0].delete()
                    self.Creator.create()
                self.Fertig = True
                self.resume()

    def switch_auto(self):
        # Wechsel zwischen Manuell und Automatik
        if self.Steuerung == 'automatisch':
            self.Steuerung = 'manuell'
        else:
            self.Steuerung = 'automatisch'
            self.resume()
    
    def update_prozesszeit(self, zeit_str):
        # Änder die Prozesszeit, falls nicht null
        zeit = int(zeit_str)
        if zeit:
            self.Prozesszeit.Value = zeit

    # OnRun-Event und exklusive Funktionen
    def OnRun(self):
        while True:
            self.suspend()
            if self.Steuerung == 'automatisch':
                # Falls Türe offen und Produkt nicht fertig bearbeitet, dann starte Prozess
                if self.istAuf and not self.Fertig:
                    self.Auf.signal(False)
                    self.Zu.signal(True)
                    self.Start.signal(True)
                # Falls Türe zu und Produkt fertig, dann Öffne Türen
                elif self.istZu and self.Fertig:
                    self.Zu.signal(False)
                    self.Start.signal(False)
                    self.Auf.signal(True)




        
    