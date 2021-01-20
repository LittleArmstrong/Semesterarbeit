#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .upvia import Upvia
from ast import literal_eval

class Roboter():
    # __init__ und alle exklusiven Funktionen (d.h. die nur hier vorkommen)
    def __init__(self, vcscript, vcrobot):
        # Konstante
        self.TYP = 'Roboter'
        # Refernz zur Applikation, Komponente und Module
        self.App = vcscript.getApplication()
        self.Komponente = vcscript.getComponent()
        self.vcrobot = vcrobot
        self.vcscript = vcscript
        # Behaviourw
        self.Container = self.Komponente.findBehavioursByType(vcscript.VC_COMPONENTCONTAINER)[0]
        # Eigenschaften
        self.Produkte = self.Komponente.getProperty('Schnittstelle::Produkte')
        # Objekt-Eigenschaften
        self.Port_anz = 0
        self.Reset_pos = [0,0,90,0,0,0]
        self.Stationen = []
        # Importierte Funktionen 
        self.update_db = Upvia().update_db
        self.resume = vcscript.resumeRun
        self.suspend = vcscript.suspendRun
        # Erstelle Behaviours und Eigenschaften falls notwendig
        self.konfig_komp(vcscript)

    # OnStart-Event und alle exklusiven Funktionen
    def OnStart(self):
        # Objekt-Eigenschaften deklariert und initialisiert
        self.Anlage = self.App.findComponent('Schnittstelle').getProperty('Schnittstelle::Anlage').Value
        if self.Anlage == 'real':
            self.Auto = True
        else:
            self.Auto = False
        self.Gelenke = None
        self.Greifen = None
        self.Komp_im_greifer = None
        self.Move_pos = None
        self.Maschine_pos = None
        self.Platzieren = None
        # Referenz zum Hilfsobjekt Roboter und den Inputs
        # Deklaration von Roboter in  __init__ nicht möglich
        self.Roboter = self.vcrobot.getRobot()
        self.Input = self.Roboter.SignalMapIn
        self.Output = self.Roboter.SignalMapOut
        if self.Anlage == 'real':
            self.Input.OnSignalTrigger = self.verwalte_signale
        # Bestimme die Stationen die Durchlaufen werden müssen
        if self.Port_anz != self.Input.PortCount:
            self.check_stationen()
        # Range-Objekt, um Route rückwärts zu betrachten und um Stationen vorher/nachher referenzieren zu können
        self.Durchlauf = range(len(self.Stationen) -2, -1, -1)
        # Referenz für die Komp. Creator
        self.Creators = self.App.findComponent('Creator')
    
    # OnSignal-Event mit allen exklusiven Funktionen
    def OnSignal(self, signal):
        if self.Anlage == 'real':
            # UpdateSignal ist ein Stringsignal. Gibt an, dass eine bestimmte Funktion aktiviert werden soll. Enthält ggf. extra Info.
            if signal.Name == 'UpdateSignal':
                update = literal_eval(signal.Value)
                # Schalte um zwischen Automatik und Manuell
                if update['Funktion'] == 'auto' and self.Anlage == 'real':
                    self.Auto = not self.Auto
                    self.resume()
                else:
                    self.Auto = False
                # Greife Komponente an gegebener Stelle. 
                if update['Funktion'] == 'greifen' or update['Funktion']=='platzieren':
                    self.update_manuell(update['Funktion'], update['Info'])
                # Platziere Komponente an gegebener Stelle.
                elif update['Funktion'] in 'bewegeGelenk+':
                    self.Gelenke = self.update_gelenke(update)
                    self.resume()
        elif self.Anlage == 'virtuell':
            if signal.Name == 'UpdateSignal':
                update = literal_eval(signal.Value)
                if update['Funktion'] == 'movePos':
                    self.Move_pos = self.update_gelenke(update)
                    self.resume()
                elif update['Funktion'] == 'maschinePos':
                    self.Maschine_pos = self.update_gelenke(update)
                    self.resume()


    # OnRun-Event mit allen exklusiven Funktionen
    def OnRun(self):
        while True:
            # Stoppt das Event. Über resume() wieder gestartet.
            self.suspend()
            # Prüfe, welche Funktion ausgeführt werden soll
            if self.Anlage == 'real':
                if self.Auto:
                    self.auto_ablauf()
                if self.Gelenke:
                    self.Roboter.driveJoints(*self.Gelenke)
                    self.Gelenke = None
                if self.Greifen:
                    iStation, komp = self.check_belegung(self.Greifen-1)
                    self.greife(iStation, komp)
                if self.Platzieren:
                    iStation, komp = self.check_belegung(self.Platzieren-1)
                    self.platziere(iStation, komp)
            elif self.Anlage == 'virtuell':
                if self.Move_pos:
                    self.next_move()   
                elif self.Maschine_pos:
                    self.next_move_maschine()
    
    def auto_ablauf(self):
        # Funktion, die für den automatischen Ablaufs des Roboters verantwortlich ist.
        # Prüft aktuelle und nächste Station, ob Komponenten vorhanden ist oder nicht.
        for i in self.Durchlauf:
            if not self.Auto:
                break
            iStation, komp = self.check_belegung(i)
            next_iStation, next_komp = self.check_belegung(i+1)
            if komp and not next_komp:
                self.greife(iStation, komp)
                self.platziere(next_iStation, next_komp)
    
    def check_belegung(self, index):
        # Funktion, die die Belegung der jeweiligen Maschine prüft, d.h. ob eine Komponente vorhanden ist oder nicht.
        iStation = self.Stationen[index]
        if iStation['Typ'] == 'Maschine':
            komp = iStation['Container'].Components
        elif iStation['Typ'] == 'Transportstelle':
            komp = iStation['Signal'].Value
        return iStation, komp
    
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
        self.Port_anz = self.Input.PortCount
    
    def greife(self, iStation, komp):
        # Führt die notwendigen Bewegungen aus, um zur Komponenten zu gelangen und greifte diese.
        # Es wird geprüft, ob eine Komponente vorhanden ist und der Greifer nicht voll ist.
        if komp and not self.Komp_im_greifer:
            # Je nach Stationstyp sind unterschiedliche Bewegungen notwendig.
            if iStation['Typ'] == 'Transportstelle':
                #self.Roboter.pickMovingPart(komp)
                self.zu_transport(komp)
                self.Komp_im_greifer = komp
            elif iStation['Typ'] == 'Maschine':
                if iStation['Offen'].Value:
                    self.zu_maschine(iStation['Station'], komp[0], 'greifen')
                    self.Komp_im_greifer = komp[0]
            self.Greifen = 0
            # Fahre zurück zur neturalen Position.
            self.Roboter.driveJoints(*self.Reset_pos)
    
    def konfig_komp(self, vcscript):
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
    
    def next_move(self):
        self.Roboter.jointMoveToPosition(*self.Move_pos [1:])
        self.Roboter.linearMoveRel(Tz=200)
        # Rest ist Vorhersage, Tx berücksichtigt Fließbandgeschwindigkeit (konst.)
        if self.Move_pos[0] == 'greifen':
            self.Output.output(1, True)
            self.Roboter.delay(0.1)
        elif self.Move_pos[0] == 'platzieren':
            self.Output.output(1,False)
            self.Roboter.delay(0.1)
        self.Move_pos = None 
        self.Roboter.moveAway()
        self.Roboter.driveJoints(*self.Reset_pos)
    
    def next_move_maschine(self):
        self.Roboter.jointMoveToPosition(*self.Maschine_pos[1:4])
        self.Roboter.jointMoveToPosition(*self.Maschine_pos[4:7])
        if self.Maschine_pos[0] == 'greifen':
            # self.Output.output(1, True)
            self.Roboter.delay(0.1)
        elif self.Maschine_pos[0] == 'platzieren':
            # self.Output.output(1,False)
            self.Roboter.delay(0.1)
        self.Maschine_pos = None
        self.Roboter.driveJoints(*self.Reset_pos)
    
    def platziere(self, iStation, next_komp):
        # Führt die notwendigen Bewegungen aus, um zur Station zu gelangen und platziert die Komponente.
        # Es wird geprüft, dass keine Komponente vorhanden ist und der Greifer voll ist.
        if self.Komp_im_greifer and not next_komp:
            # Je nach Stationstyp sind unterschiedliche Bewegungen notwendig.
            if iStation['Typ'] == 'Transportstelle':
                #self.Roboter.place(iStation['Station'])
                self.zu_transport(self.Komp_im_greifer, iStation['Station'])
                self.Komp_im_greifer = None
            elif iStation['Typ'] == 'Maschine' and iStation['Offen'].Value:
                self.zu_maschine(iStation['Station'], self.Komp_im_greifer, 'platzieren')
                self.Komp_im_greifer = None
            if not self.Komp_im_greifer:
                self.update_db(self.Komponente.Name, self.TYP, 'komp', '')
            self.Platzieren = 0
            # Fahre zurück zur neturalen Position.
            self.Roboter.driveJoints(*self.Reset_pos)
        
    def update_gelenke(self, update):
        # Gibt an, welche Werte die Gelenke annehmen sollen
        relativ = False
        gelenke = []
        werte = literal_eval(update['Info'])
        if update['Funktion'] == 'bewegeGelenk+':
            relativ = True
        elif update['Funktion'] == 'movePos' or update['Funktion'] == 'maschinePos':
            gelenke = [werte[0]]
            werte = werte[1:]
        gelenke += [int(wert) for wert in werte] + [0, relativ]
        return gelenke
    
    def update_manuell(self, funktion, info):
        # Gibt an, wo gegriffen/platziert werden soll
        station_index = int(info)
        if 0 <= station_index <= len(self.Stationen):
            if funktion == 'platzieren':
                self.Platzieren = station_index
            elif funktion == 'greifen':
                self.Greifen = station_index
            self.resume()
    
    def update_pos_maschine(self, move, station):
        pos = station.WorldPositionMatrix
        frame1_mtx = station.findFeature('ProductLocationApproach').FramePositionMatrix
        frame2_mtx = station.findFeature('ProcessLocation').FramePositionMatrix
        frame1_weltpos = pos * frame1_mtx
        frame2_weltpos = pos * frame2_mtx
        pos1 = (frame1_weltpos.P.X, frame1_weltpos.P.Y, frame1_weltpos.P.Z)
        pos2 = (frame2_weltpos.P.X, frame2_weltpos.P.Y, frame2_weltpos.P.Z)
        pos = (move,) + pos1 + pos2
        self.update_db(self.Komponente.Name, self.TYP, 'maschinePos', repr(pos))
    
    def update_pos_transport(self, height, komp, station=None):
        if station:
            pos = ('platzieren', station.WorldPositionMatrix.P.X, station.WorldPositionMatrix.P.Y, station.WorldPositionMatrix.P.Z+height+200)
        elif komp:
            pos = ('greifen', komp.WorldPositionMatrix.P.X, komp.WorldPositionMatrix.P.Y, komp.WorldPositionMatrix.P.Z+height+200)
        else:
            return
        self.update_db(self.Komponente.Name, self.TYP, 'movePos', repr(pos))


    def verwalte_signale(self, signal_map, port, bool_wert):
        # Ist eins der Inputsignal positiv, so wird das OnRun-Event wieder gestartet
        # Signaliert, wenn eine Komponente die Transportstelle durchfährt oder die Türe der Maschine öffnen
        if bool_wert:
            self.resume()
    
    def zu_maschine(self, station, komp, move):
        # Anfahrt zur Maschine
        # Frame 'ProcessLocation' muss im Root-Feature der Root-Komponente, d.h. 'ganz oben' erstellt werden
        # Obige Frame sollte an der gleichen Stelle wie die Frame 'ProductLocation' sein
        self.update_pos_maschine(move, station)
        self.Roboter.jointMoveToComponent(station, ToFrame = 'ProductLocationApproach')
        self.Roboter.jointMoveToComponent(station, ToFrame = 'ProcessLocation')
        if move == 'greifen':
            self.Roboter.graspComponent(komp)
        elif move == 'platzieren':
            self.Roboter.releaseComponent(station)
    
    def zu_transport(self, komp, station = None):
        height = komp.BoundCenter.length() * 2
        if not self.Anlage=='real':
            return
        self.update_pos_transport(height, komp, station)
        if not station:
            height=0
        self.Roboter.jointMoveToComponent(station or komp, Tz=200+height , OnFace='top')
        self.Roboter.linearMoveToComponent(station or komp, Tx=70, Tz=height, OnFace='top')
        if station:
            self.Roboter.releaseComponent(station)
        elif komp:
            self.Roboter.graspComponent(komp)
        self.Roboter.delay(0.1)
        self.Roboter.moveAway()


                    

            

   