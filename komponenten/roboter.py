#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .datenbank import Datenbank
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
        # Referenz zu Modulen
        self.vcrobot = vcrobot
        self.vcscript = vcscript
        # Importierte Funktionen 
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
        # Referenz zum Hilfsobjekt Roboter und den Inputs
        # Deklaration von Roboter in  __init__ aus irgendeinem Grund nicht möglich
        self.Roboter = self.vcrobot.getRobot()
        self.Input = self.Roboter.SignalMapIn
        self.Input.OnSignalTrigger = self.verwalte_signale
        # Objekt-Eigenschaften deklariert und initialisiert
        self.Automatisch = True        
        self.Gelenkwerte = None
        self.Komponente_im_greifer = None
        self.Manuell_greifen = 0
        self.Manuell_platzieren = 0
        self.Relativ = False
        self.Stationen = []
        # Bestimme die Stationen die Durchlaufen werden müssen
        self.ermittle_stationen()
        # Range-Objekt, um Route rückwärts zu betrachten und um Stationen vorher/nachher referenzieren zu können
        self.Durchlauf = range(len(self.Stationen) -2, -1, -1)
    
    def ermittle_stationen(self):
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
        # UpdateSignal ist ein Stringsignal. Gibt an, dass eine bestimmte Funktion aktiviert werden soll. Enthält ggf. extra Info.
        if signal.Name == 'UpdateSignal':
            update = literal_eval(signal.Value)
            # Schalte um zwischen Automatik und Manuell
            if update['Funktion'] == 'auto':
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
            if self.Automatisch:
                self.auto_ablauf()
            if self.Gelenkwerte:
                self.Roboter.driveJoints(*self.Gelenkwerte)
                self.Gelenkwerte = None
            if self.Manuell_greifen:
                iStation, komp =  self.ermittle_belegung(self.Manuell_greifen-1)
                self.greife_komponente(iStation, komp)
            if self.Manuell_platzieren:
                iStation, komp =  self.ermittle_belegung(self.Manuell_platzieren-1)
                self.platziere_komponente(iStation, komp)
            if self.Komponente_im_greifer:
                self.Manuell_greifen = 0
            else:
                self.Manuell_platzieren = 0
    
    def auto_ablauf(self):
        # Funktion, die für den automatischen Ablaufs des Roboters verantwortlich ist.
        # Prüft aktuelle und nächste Station, ob Komponenten vorhanden ist oder nicht.
        for i in self.Durchlauf:
            if not self.Automatisch:
                break
            iStation, komp = self.ermittle_belegung(i)
            next_iStation, next_komp = self.ermittle_belegung(i+1)
            if komp and not next_komp:
                self.greife_komponente(iStation, komp)
                self.platziere_komponente(next_iStation, next_komp)
    
    def ermittle_belegung(self, index):
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
                self.Roboter.pickMovingPart(komp)
                self.Komponente_im_greifer = komp
            elif iStation['Typ'] == 'Maschine':
                if iStation['Offen'].Value:
                    self.zu_maschine(iStation['Station'], komp[0], 'greifen')
                    self.Komponente_im_greifer = komp[0]
            # Fahre zurück zur neturalen Position.
            self.Roboter.driveJoints(0,0,90,0,0,0)

    def platziere_komponente(self, iStation, next_komp):
        # Führt die notwendigen Bewegungen aus, um zur Station zu gelangen und platziert die Komponente.
        # Es wird geprüft, dass keine Komponente vorhanden ist und der Greifer voll ist.
        if self.Komponente_im_greifer and not next_komp:
            # Je nach Stationstyp sind unterschiedliche Bewegungen notwendig.
            if iStation['Typ'] == 'Transportstelle':
                self.Roboter.place(iStation['Station'])
                self.Komponente_im_greifer = None
            elif iStation['Typ'] == 'Maschine':
                if iStation['Offen'].Value:
                    self.zu_maschine(iStation['Station'], self.Komponente_im_greifer, 'platzieren')
                    self.Komponente_im_greifer = None
            # Fahre zurück zur neturalen Position.
            self.Roboter.driveJoints(0,0,90,0,0,0)

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
        

                    

            

   