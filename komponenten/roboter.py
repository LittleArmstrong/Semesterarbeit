#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .datenbank import Datenbank
from .upvia import Upvia
import konstanten
from ast import literal_eval

class Roboter():
    # __init__ und alle exklusiven Funktionen (d.h. die nur hier vorkommen)
    def __init__(self, vcscript, vcrobot):
        # Konstante
        self.TYP = 'Roboter'
        # Refernz zur Applikation und Komponente
        self.App = vcscript.getApplication()
        self.Komponente = vcscript.getComponent()
        # Referenz zu Module
        self.vcrobot = vcrobot
        self.vcscript = vcscript
        # Eigenschaften
        self.Produkte = self.Komponente.getProperty('Schnittstelle::Produkte')
        # Objekt-Eigenschaften
        self.Reset_pos = [0,0,90,0,0,0]
        # Importierte Funktionen 
        self.update_db = Upvia().update_db
        self.resume = vcscript.resumeRun
        self.suspend = vcscript.suspendRun
        # Erstelle Behaviours und Eigenschaften falls notwendig
        self.konfiguriere_komponente(vcscript)
    
    def konfiguriere_komponente(self, vcscript):
        # Referenz zum Pythonscript selbst
        script = self.Komponente.findBehaviour('Script')
        # Behaviours
        # - UpdateSignal, um Befehle erhalten zu können
        if not self.Komponente.findBehaviour('UpdateSignal'):
            update_signal = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
            update_signal.Connections = [script]
        # Eigenschaften
        # - Typ, um Komponente und dessen Funktion zu erkennen
        if not self.Komponente.getProperty('Schnittstelle::Typ'):
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP
    
    # OnStart-Event und alle exklusiven Funktionen
    def OnStart(self):
        # Objekt-Eigenschaften deklariert und initialisiert
        self.Anlage = self.App.findComponent('Schnittstelle').getProperty('Schnittstelle::Anlage').Value
        if self.Anlage == 'real':
            self.Automatisch = True
        else:
            self.Automatisch = False
        self.Gelenkwerte = None
        self.Greifen = None
        self.Komponente_im_greifer = None
        self.Manuell_greifen = 0
        self.Manuell_platzieren = 0
        self.Platzieren = None
        self.Relativ = False
        self.Stationen = []
        # Referenz zum Hilfsobjekt Roboter und den Inputs
        # Deklaration von Roboter in  __init__ nicht möglich
        self.Roboter = self.vcrobot.getRobot()
        self.Input = self.Roboter.SignalMapIn
        self.Output = self.Roboter.SignalMapOut
        if self.Anlage == 'real':
            self.Input.OnSignalTrigger = self.verwalte_signale
        # Bestimme die Stationen die Durchlaufen werden müssen
        self.check_stationen()
        # Range-Objekt, um Route rückwärts zu betrachten und um Stationen vorher/nachher referenzieren zu können
        self.Durchlauf = range(len(self.Stationen) -2, -1, -1)
    
    def check_stationen(self):
        # Durchlaufe die Ports (Input) des Roboters
        ports = self.Input.getAllConnectedPorts()
        for port in ports:
            # Port 150 bis 159 sind für die Stationen reserviert
            if not (150 <= port < 160):
                continue
            station = self.Input.getConnectedExternalSignals(port)[0].Component
            typ = station.getProperty('Schnittstelle::Typ').Value
            # Unterscheide zwischen Transport- und Bearbeitungsstelle (Maschine)
            # Speichere notwendige Informationen zum greifen und platzieren
            if typ == 'Maschine':
                container = station.findBehavioursByType(self.vcscript.VC_COMPONENTCONTAINER)[0]
                offen = station.findBehaviour('TO_PLC_DoorIsOpen')
                iStation = {'Station':station,'Typ': typ, 'Container':container, 'Offen': offen}
            elif typ == 'Transportstelle':
                signal = station.findBehaviour('SensorComponentSignal')
                iStation = {'Station':station,'Typ': typ, 'Signal':signal}
            self.Stationen.append(iStation)
        
    # OnSignal-Event mit allen exklusiven Funktionen
    def OnSignal(self, signal):
        if self.Anlage == 'real':
            # UpdateSignal ist ein Stringsignal. Gibt an, dass eine bestimmte Funktion aktiviert werden soll. Enthält ggf. extra Info.
            if signal.Name == 'UpdateSignal':
                update = literal_eval(signal.Value)
                # Schalte um zwischen Automatik und Manuell
                if update['Funktion'] == 'auto' and self.Anlage == 'real':
                    self.Automatisch = not self.Automatisch
                    self.resume()
                else:
                    self.Automatisch = False
                # Greife Komponente an gegebener Stelle. Schaltet um auf Manuell
                if update['Funktion'] == 'greifen' or update['Funktion']=='platzieren':
                    self.update_manuell(update['Funktion'], update['Info'])
                # Platziere Komponente an gegebener Stelle. Schaltet um auf Manuell
                elif update['Funktion'] in 'bewegeGelenk+':
                    self.update_gelenkwerte(update)
        elif self.Anlage == 'virtuell':
            if signal.Name == 'UpdateSignal':
                update = literal_eval(signal.Value)
                if update['Funktion'] == 'greifen':
                    self.Greifen = literal_eval(update['Info'])
                    self.resume()
                elif update['Funktion'] == 'platzieren':
                    self.Platzieren = literal_eval(update['Info'])
                    self.resume()

    def update_gelenkwerte(self, update):
        # Gibt an, welche Werte die Gelenke einnehmen sollen
        if update['Funktion'] == 'bewegeGelenk+':
            self.Relativ = True
        else:
            self.Relativ = False
        self.Gelenkwerte = [int(wert) for wert in literal_eval(update['Info'])] + [0, self.Relativ]
        self.resume()

    def update_manuell(self, funktion, info):
        # Gibt an, wo gegriffen/platziert werden soll
        station_index = int(info)
        if 0 <= station_index <= len(self.Stationen):
            if funktion == 'platzieren':
                self.Manuell_platzieren = station_index
            elif funktion == 'greifen':
                self.Manuell_greifen = station_index
            self.resume()
    
    # OnRun-Event mit allen exklusiven Funktionen
    def OnRun(self):
        while True:
            # Stoppt das Event. Über resume() wieder gestartet.
            self.suspend()
            # Prüfe, welche Funktion ausgeführt werden soll
            if self.Anlage == 'real':
                if self.Automatisch:
                    self.auto_ablauf()
                if self.Gelenkwerte:
                    self.Roboter.driveJoints(*self.Gelenkwerte)
                    self.Gelenkwerte = None
                if self.Manuell_greifen:
                    iStation, komp =  self.check_belegung(self.Manuell_greifen-1)
                    self.greife_komponente(iStation, komp)
                if self.Manuell_platzieren:
                    iStation, komp =  self.check_belegung(self.Manuell_platzieren-1)
                    self.platziere_komponente(iStation, komp)
            elif self.Anlage == 'virtuell':
                if self.Greifen:
                    #self.Roboter.driveJoints(*self.Greifen)
                    self.Roboter.jointMoveToPosition(*self.Greifen)
                    self.Roboter.linearMoveRel(Tx=-200, Tz=200)
                    self.Output.output(1, True)
                    self.Roboter.delay(0.1)
                    self.Roboter.moveAway()
                    self.Roboter.driveJoints(*self.Reset_pos)
                    self.Greifen = None
                elif self.Platzieren:
                    #self.Roboter.driveJoints(*self.Platzieren)
                    self.Roboter.jointMoveToPosition(*self.Platzieren)
                    self.Roboter.linearMoveRel(Tz=200)
                    self.Output.output(1,False)
                    self.Roboter.delay(0.1)
                    self.Roboter.moveAway()
                    self.Roboter.driveJoints(*self.Reset_pos)
                    self.Platzieren = None


    def auto_ablauf(self):
        # Funktion, die für den automatischen Ablaufs des Roboters verantwortlich ist.
        # Prüft aktuelle und nächste Station, ob Komponenten vorhanden ist oder nicht.
        for i in self.Durchlauf:
            if not self.Automatisch:
                break
            iStation, komp = self.check_belegung(i)
            next_iStation, next_komp = self.check_belegung(i+1)
            print(i, komp, next_komp)
            if komp and not next_komp:
                self.greife_komponente(iStation, komp)
                self.platziere_komponente(next_iStation, next_komp)
    
    def check_belegung(self, index):
        # Funktion, die die Belegung der jeweiligen Maschine prüft, d.h. ob eine Komponente vorhanden ist oder nicht.
        iStation = self.Stationen[index]
        if iStation['Typ'] == 'Maschine':
            komp = iStation['Container'].Components
        elif iStation['Typ'] == 'Transportstelle':
            komp = iStation['Signal'].Value
        return iStation, komp

    def greife_komponente(self, iStation, komp):
        # Führt die notwendigen Bewegungen aus, um zur Komponenten zu gelangen und greifte diese.
        # Es wird geprüft, ob eine Komponente vorhanden ist und der Greifer nicht voll ist.
        if komp and not self.Komponente_im_greifer:
            # Je nach Stationstyp sind unterschiedliche Bewegungen notwendig.
            if iStation['Typ'] == 'Transportstelle':
                #self.Roboter.pickMovingPart(komp)
                self.zu_transport(komp)
                self.Komponente_im_greifer = komp
            elif iStation['Typ'] == 'Maschine':
                if iStation['Offen'].Value:
                    self.zu_maschine(iStation['Station'], komp[0], 'greifen')
                    self.Komponente_im_greifer = komp[0]
            self.Manuell_greifen = 0
            # Fahre zurück zur neturalen Position.
            self.Roboter.driveJoints(*self.Reset_pos)

    def platziere_komponente(self, iStation, next_komp):
        # Führt die notwendigen Bewegungen aus, um zur Station zu gelangen und platziert die Komponente.
        # Es wird geprüft, dass keine Komponente vorhanden ist und der Greifer voll ist.
        if self.Komponente_im_greifer and not next_komp:
            # Je nach Stationstyp sind unterschiedliche Bewegungen notwendig.
            if iStation['Typ'] == 'Transportstelle':
                #self.Roboter.place(iStation['Station'])
                self.zu_transport(self.Komponente_im_greifer, iStation['Station'])
                self.Komponente_im_greifer = None
            elif iStation['Typ'] == 'Maschine':
                if iStation['Offen'].Value:
                    self.zu_maschine(iStation['Station'], self.Komponente_im_greifer, 'platzieren')
                    self.Komponente_im_greifer = None
            self.Manuell_platzieren = 0
            # Fahre zurück zur neturalen Position.
            self.Roboter.driveJoints(*self.Reset_pos)
    
    def update_virtuelle_gelenkwerte(self):
        if self.Anlage == 'real':
            gelenkwerte =[g.CurrentValue for g in self.Roboter.Joints]
            self.update_db(self.Komponente.Name, self.TYP, 'platzieren', repr(gelenkwerte))


    def verwalte_signale(self, signal_map, port, bool_wert):
        # Ist eins der Inputsignal positiv, so wird das OnRun-Event wieder gestartet
        # Signaliert, wenn eine Komponente die Transportstelle durchfährt oder die Türe der Maschine öffnen
        if bool_wert:
            self.resume()
    
    def zu_maschine(self, station, komp, funktion):
        # Anfahrt zur Maschine
        # Frame 'ProcessLocation' muss im Root-Feature der Root-Komponente, d.h. 'ganz oben' erstellt werden
        # Obige Frame sollte an der gleichen Stelle wie die Frame 'ProductLocation' sein
        self.Roboter.jointMoveToComponent(station, ToFrame = 'ProductLocationApproach')
        self.Roboter.jointMoveToComponent(station, ToFrame = 'ProcessLocation')
        if funktion == 'greifen':
            self.Roboter.graspComponent(komp)
        elif funktion == 'platzieren':
            self.Roboter.releaseComponent(station)
    
    def zu_transport(self, komp, station = None):
        height = komp.BoundCenter.length() * 2
        if station and self.Anlage=='real':
            pos = [station.WorldPositionMatrix.P.X, station.WorldPositionMatrix.P.Y, station.WorldPositionMatrix.P.Z+height+200]
            self.update_db(self.Komponente.Name, self.TYP, 'platzieren', repr(pos))
        elif self.Anlage == 'real':
            pos = [komp.WorldPositionMatrix.P.X, komp.WorldPositionMatrix.P.Y, komp.WorldPositionMatrix.P.Z+height+200]
            self.update_db(self.Komponente.Name, self.TYP, 'greifen', repr(pos))
            height=0
        self.Roboter.jointMoveToComponent(station or komp, Tz=200+height , OnFace='top')
        self.update_virtuelle_gelenkwerte()
        self.Roboter.linearMoveToComponent(station or komp, Tx=70, Tz=height, OnFace='top')
        if station:
            self.Roboter.releaseComponent(station)
        else:
            self.Roboter.graspComponent(komp)
        self.Roboter.delay(0.1)
        self.Roboter.moveAway()

                    

            

   