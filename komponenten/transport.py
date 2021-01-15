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
        # Eigenschaften der Komponente
        self.Produkte = self.Komponente.getProperty('Schnittstelle::Produkte')
        # - Event bei Änderung
        if self.Produkte:
            self.Produkte.OnChanged = self.synchronisiere_produkte
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
        if not self.Sensor.Frame:
            index_frame = int(len(self.Path.Path)/2)
            frame = self.Path.Path[index_frame]
            self.Sensor.Frame = frame
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
        # - Produkte, die auf Fließband laufen
        if not self.Produkte:
            self.Produkte = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Produkte')
            self.Produkte.OnChanged = self.synchronisiere_produkte
    
    def synchronisiere_produkte(self, prod):
        # Wird die Eigenschaft Produkte bei einem Förderband verändert, dann auch bei allen verbundenen
        iface = ['InInterface', 'OutInterface']
        for i in iface:
            verbundene_komp = self.Komponente.findBehaviour(i).ConnectedComponent
            while verbundene_komp:
                produkte = verbundene_komp.getProperty('Schnittstelle::Produkte')
                if produkte.Value != prod.Value:
                    produkte.Value = prod.Value
                    verbundene_komp = verbundene_komp.findBehaviour(i).ConnectedComponent
                else:
                    verbundene_komp = None
    # OnStart-Event
    def OnStart(self):
         # Beim Kurven-Rollband wird die Sensorposition aus irgendeinem Grund resettet, deswegen wird er hier neu zugewiesen
         # ! Kurven-Rollband nicht kopieren, sondern einzeln in das Layout platzieren, da sonst die frames sich beim Pfad
         # aus irgendeinem Grund ändern !
        if not self.Sensor.Frame:
            index_frame = int(len(self.Path.Path)/2)
            frame = self.Path.Path[index_frame]
            self.Sensor.Frame = frame
        # Variablen zur Bestimmung der Sensorposition
        path_anfang = self.Path.Path[0].FramePositionMatrix.P
        sensor_position = self.Sensor.Frame.FramePositionMatrix
        komp_position = self.Komponente.PositionMatrix
        # Objekt-Eigenschaften
        self.Anlage = self.App.findComponent('Schnittstelle').getProperty('Schnittstelle::Anlage').Value
        self.Aktuelle_komp = None
        self.Creators = self.ermittle_creators()
        self.Erstellte_komponente = None
        self.Produktname = None
        self.Real = False
        self.Sensor_path_distanz = (sensor_position.P - path_anfang).length()
        self.Sensor_weltposition = komp_position * sensor_position
        self.Umleiten = None
        self.Virtuell = False
    
    def ermittle_creators(self):
        produkte = self.Produkte.Value
        alle_creator = None
        creators = {}
        # Erstelle abh. von Produktanzahl ComponentCreator
        if produkte:
            produkte = produkte.split(',')
            alle_creator = self.Komponente.findBehavioursByType(self.Vcscript.VC_COMPONENTCREATOR)
            diff = len(alle_creator) - len(produkte)
            if diff < 0:
                for i in range(diff*-1):
                    creator = self.Komponente.createBehaviour(self.Vcscript.VC_COMPONENTCREATOR, str(i))
                    creator.Limit = 0
                    creator.Interval = 0
                alle_creator = self.Komponente.findBehavioursByType(self.Vcscript.VC_COMPONENTCREATOR)
        # Speichere die ComponentCreator in einem Wörterbuch mit dem Produktnamen, das hergestellt wird, als Index
        for i, produkt in enumerate(produkte):
            creator = alle_creator[i]
            if creator.Name != produkt + '__HIDE__':
                creator.Name = produkt + '__HIDE__'
                uri = self.App.findComponent(produkt).Uri
                creator.Part = uri
            creators[produkt] = creator
        return creators

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
                    self.vergleiche_virtuell(update['Info'])
            # KompSignal signalisert Komponenten auf dem Pfad/Sensor
            elif signal == self.Komp_signal:
                self.vergleiche_real()
        elif self.Anlage == 'real':
            if signal.Name == 'UpdateSignal':
                update = literal_eval(signal.Value)
                if update['Funktion'] == 'umleiten':
                    # Untersucht, ob umgeleitet werden soll und wohin und speichert die Info
                    self.update_umleite(update['Info'])
                elif update['Funktion'] == 'erstelle':
                    # Erstellt Komponente
                    self.Produktname = update['Info']
                    self.erstelle_komponente()
            elif signal == self.Komp_signal and signal.Value:
                # Falls umgeleitet werden soll, entferne Komp und erstelle neue am jeweiligen Fließband
                if self.Umleiten:
                    self.umleite_komp(signal.Value)
                # Wenn nicht, dann sende ein Signal an die virtuelle Anlage, dass ein Produkt hier ist
                else:
                    self.update_db('signal', signal.Value.Name)

    def entferne_komponente(self):
        # Entferne nächste Komponente vor Sensor, falls existiert
        komps = self.Path.Components
        if not komps:
            return
        komps_distanz = [self.Sensor_path_distanz - komp.getPathDistance() for komp in komps]
        pos_distanz = [dist for dist in komps_distanz if dist>0]
        if not pos_distanz:
            return
        index = komps_distanz.index(min(pos_distanz))
        komp = komps[index]
        komp.delete()

    def erstelle_komponente(self):
        # Erstelle Komponente am Sensor
        creator = self.Creators[self.Produktname]
        self.Container.getConnector('Input').connect(creator.getConnector('Output'))
        komp = creator.create()
        komp.PositionMatrix = self.Sensor_weltposition
        self.Path.grab(komp)
        return komp

    def umleite_komp(self, komp):
        # Sende ein Signal zum Fließband, zu der umgeleitet werden. Erstelle dort Komponente und entferne hier Komponente
        info = repr({'Funktion':'erstelle', 'Info': komp.Name})
        self.Umleiten.signal(info)
        komp.delete()
    
    def update_db(self, funktion, wert):
        # Aktualisiere die Datenbank. Signale gelangen so zur virtuellen Anlage.
        db = Datenbank(self.DB_PFAD)
        parameter = (self.Komponente.Name, self.TYP, funktion, wert)
        db.replace_query(self.DB_TABELLE, parameter)
    
    def update_umleite(self, zu_komp):
        # Lege fest ob umgeleitet werden soll oder nicht und wohin und speichere die Info
        update = self.App.findComponent(zu_komp).findBehaviour('UpdateSignal')
        if update != self.Umleiten:
            self.Umleiten = update
        else:
            self.Umleiten = None
    
    def vergleiche_real(self):
        # Warte bis Komponente über Signal. Speicher Komponente solange
        if self.Komp_signal.Value:
            self.Virtuell = True
            self.Aktuelle_komp = self.Komp_signal.Value
        else:
            # Entferne Komponente, falls nicht selbst erstellt oder kein Signal von realer Anlage
            if self.Aktuelle_komp and not self.Real and self.Aktuelle_komp != self.Erstellte_komponente:
                self.Aktuelle_komp.delete()
                self.Aktuelle_komp = None
            self.Virtuell = False
            self.Real = False

    def vergleiche_virtuell(self, produkt):
        # Erhalte Names des Produkts aus der realen Anlage, damit dieser in der virtuellen Anlage hergestellt werden kann
        self.Produktname = produkt
        self.Real = True
        # Erstelle Produkt, falls bei der virtuellen Anlage der Sensor nicht aktiviert wurde und entferne nächste Komp zum Sensor
        if not self.Virtuell:
            self.Erstellte_komponente = self.erstelle_komponente()
            self.entferne_komponente()
            self.Real = False
            
    def OnRun(self):
        pass
        


        

    
            
        
        



        
        
