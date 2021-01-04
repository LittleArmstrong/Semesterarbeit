#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .datenbank import Datenbank
import konstanten
from ast import literal_eval

class Roboter():
    def __init__(self, vcscript, vcrobot):
        self.TYP = 'Roboter'

        self.Komponente = vcscript.getComponent()
        self.vcrobot = vcrobot
        self.App = vcscript.getApplication()
        self.Roboter = None
        self.Signal_input = None

        self.Updatesignal = self.Komponente.findBehaviour('UpdateSignal')

        self.konfiguriere_komponente(vcscript)

        self.Ist_automatisch = True
        self.Greifsignal = None
        self.Ablegeplatz = None
        self.Zu_ergreifende_komponente = None
        self.Ergriffene_komponente = None

        self.Greife_manuell = False
        self.Platziere_manuell = False

        self.Gelenkwerte = None
        self.Relativ = False

        self.Route_ports = None
        self.Route = None
        self.Komponente_in_maschine = None

        self.suspend = vcscript.suspendRun
        self.resume = vcscript.resumeRun

    def OnStart(self):
        self.Roboter = self.vcrobot.getRobot()
        self.Signal_input = self.Roboter.SignalMapIn
        self.Signal_input.OnSignalTrigger = self.ermittle_zu_ergreifende_komponente

        self.Ergriffene_komponente = None
        self.Zu_ergreifende_komponente = None
        self.Komponente_auf_route = None

        self.Ist_automatisch = True
        self.Komponente_in_maschine = None

        self.ermittle_route()

        self.Greifsignal = self.ermittle_greifsignal()
        #self.Ablegeplatz = self.ermittle_ablegeplatz()


    def OnSignal(self, signal):
        if signal == self.Updatesignal:
            update = literal_eval(signal.Value)
            if update['Funktion'] == 'auto':
                self.Ist_automatisch = not self.Ist_automatisch
            elif update['Funktion'] == 'greifen':
                self.Ist_automatisch = False
                self.Greife_manuell = True
            elif update['Funktion'] == 'platzieren':
                self.Ist_automatisch = False
                self.Platziere_manuell = True
                self.resume()
            elif 'bewegeGelenk' in update['Funktion']:
                if update['Funktion'] == 'bewegeGelenk+':
                    self.Relativ = True
                else:
                    self.Relativ = False
                self.Ist_automatisch = False
                self.Gelenkwerte = literal_eval(update['Info'])
                self.resume()

    def OnRun(self):
        self.ermittle_route()
        while True:
            self.suspend()
            if self.Ist_automatisch:
                self.ergreife_komponente()
                self.platziere_komponente()

            if self.Greife_manuell:
                self.ergreife_komponente()
                self.Greife_manuell = False
            elif self.Platziere_manuell:
                self.platziere_komponente()
                self.Platziere_manuell = False

            if self.Gelenkwerte:
                g1 = self.Gelenkwerte['G1'] 
                g2 = self.Gelenkwerte['G2'] 
                g3 = self.Gelenkwerte['G3'] 
                g4 = self.Gelenkwerte['G4'] 
                g5 = self.Gelenkwerte['G5'] 
                g6 = self.Gelenkwerte['G6'] 
                self.Roboter.driveJoints(g1, g2, g3, g4, g5, g6, 0, self.Relativ)
                self.Gelenkwerte = None

    def konfiguriere_komponente(self, vcscript):
        if not self.Updatesignal:
            script = self.Komponente.findBehaviour('Script')
            self.Updatesignal = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
            self.Updatesignal.Connections = [script]

        if not self.Komponente.getProperty('Schnittstelle::Typ'):
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP

    def ermittle_zu_ergreifende_komponente(self, signal_map, port, bool_wert):
        if port == 150 and signal_map.input(150):
            self.Zu_ergreifende_komponente = self.Greifsignal.Value
            self.Ablegeplatz = self.Route[1]
            self.resume()
        elif port == 151 and signal_map.input(151):
            self.Ablegeplatz = self.Route[2]
            self.resume()
        elif port == 300 and not signal_map.input(300):
            self.mach_maschine_auf()
        
    def ergreife_komponente(self):
        if self.Ist_automatisch and not self.Ergriffene_komponente:
            signal_maschine_auf = self.Ablegeplatz.findBehaviour('TO_PLC_DoorIsOpen')
            if not self.Komponente_in_maschine:
                self.Roboter.pickMovingPart(self.Zu_ergreifende_komponente)
                self.Ergriffene_komponente = self.Zu_ergreifende_komponente
                self.Roboter.driveJoints(0,0,90,0,0,0)
            elif self.Komponente_in_maschine and signal_maschine_auf.Value:
                self.ergreife_komponente_maschine()
    
    def platziere_komponente(self):
        if self.Ist_automatisch and self.Ergriffene_komponente:
            ablegeplatz_typ = self.Ablegeplatz.getProperty('Schnittstelle::Typ').Value
            if ablegeplatz_typ == 'Transport':
                self.Roboter.place(self.Ablegeplatz)
                self.Ergriffene_komponente = None
            elif ablegeplatz_typ == 'Maschine':
                signal_maschine_offen = self.Ablegeplatz.findBehaviour('TO_PLC_DoorIsOpen')
                if signal_maschine_offen.Value:
                    self.platziere_maschine()
                    self.erstelle_verbindung_zu_maschine()
                    self.Komponente_in_maschine = self.Ablegeplatz
                    self.Ergriffene_komponente = None
            self.Ergriffene_komponente = None
            self.Roboter.driveJoints(0,0,90,0,0,0)
    
    def ermittle_greifsignal(self):
        rollband_bool_signal = self.Signal_input.getConnectedExternalSignals(150)[0]
        rollband = rollband_bool_signal.Component
        return rollband.findBehaviour('SensorSignal')

    def ermittle_ablegeplatz(self):
        rollband_bool_signal = self.Signal_input.getConnectedExternalSignals(151)[0]
        return rollband_bool_signal.Component
    
    def ermittle_route(self):
        self.Route_ports = [port for port in self.Signal_input.getAllConnectedPorts() if port >=150]
        self.Route = []

        for port in self.Route_ports:
            externes_signal = self.Signal_input.getConnectedExternalSignals(port)[0]
            externe_komponente = externes_signal.Component
            self.Route.append(externe_komponente)

    def platziere_maschine(self):
        self.Roboter.jointMoveToComponent(self.Ablegeplatz, ToFrame = 'ProductLocationApproach')
        self.Roboter.jointMoveToComponent(self.Ablegeplatz, Rx=-90, Ty=self.Ergriffene_komponente.BoundCenter.length() * 2, ToFrame='ResourceLocation')
        self.Roboter.releaseComponent(self.Ablegeplatz)
        self.Roboter.driveJoints(0,0,90,0,0,0)
        signal_maschine_zu = self.Ablegeplatz.findBehaviour('FROM_PLC_CloseDoor')
        signal_maschine_zu.signal(True)
        signal_prozess_starten = self.Ablegeplatz.findBehaviour('FROM_PLC_StartProcess')
        signal_prozess_starten.signal(True)

    def erstelle_verbindung_zu_maschine(self):
        signal = self.Ablegeplatz.findBehaviour('TO_PLC_ProcessIsRunning')
        self.Signal_input.connect(300, signal)

    def mach_maschine_auf(self):
        signal = self.Ablegeplatz.findBehaviour('FROM_PLC_OpenDoor')
        signal.signal(True)
        self.Signal_input.disconnect(300)

    def ergreife_komponente_maschine(self):
        self.Roboter.jointMoveToComponent(self.Komponente_in_maschine, ToFrame = 'ProductLocationApproach')
        self.Roboter.jointMoveToComponent(self.Komponente_in_maschine, Rx=-90, Ty=self.Zu_ergreifende_komponente.BoundCenter.length() * 2, ToFrame='ResourceLocation')
        self.Roboter.graspComponent(self.Zu_ergreifende_komponente)
        self.Roboter.driveJoints(0,0,90,0,0,0)




