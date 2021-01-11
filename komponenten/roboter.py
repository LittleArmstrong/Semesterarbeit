#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .datenbank import Datenbank
import konstanten
from ast import literal_eval

class Roboter():
    def __init__(self, vcscript, vcrobot):
        self.TYP = 'Roboter'

        self.App = vcscript.getApplication()
        self.Komponente = vcscript.getComponent()
        self.vcrobot = vcrobot

        self.Produktzustand = self.Komponente.getProperty('Schnittstelle::Produktzustand')
        
        self.konfiguriere_komponente(vcscript)
        
        self.Anz_container = 0
        self.Automatisch = True
        self.Buffer = []
        self.Gelenkwerte = None
        self.Roboter = None
        self.Komponente_im_greifer = None
        self.Komponenten_auf_route = []
        self.Komponenten_sensor = None
        self.Manuell_greifen = 0
        self.Manuell_platzieren = 0
        self.Maschinen = []
        self.Relativ = False
        self.Route = []
        self.Route_ports = []
        self.Route_range = None
        self.Signal_input = None
        
        self.suspend = vcscript.suspendRun
        self.resume = vcscript.resumeRun

    def OnStart(self):
        self.Roboter = self.vcrobot.getRobot()
        self.Signal_input = self.Roboter.SignalMapIn
        self.Signal_input.OnSignalTrigger = self.verwalte_signale
        self.Komponenten_sensor = self.Signal_input.getConnectedExternalSignals(150)[0].Component.findBehaviour('SensorSignal')

        self.ermittle_route()
        self.ermittle_maschinen()

        self.Anz_container = len(self.Komponenten_auf_route)
        self.Automatisch = True
        self.Buffer = []
        self.Gelenkwerte = None
        self.Komponenten_auf_route = [None for komp in self.Route]
        self.Komponente_im_greifer = None
        self.Manuell_greifen = 0
        self.Manuell_platzieren = 0
        self.Route_range = range(self.Anz_container -2, -1, -1)

    def OnSignal(self, signal):
        if signal.Name == 'UpdateSignal':
            update = literal_eval(signal.Value) 
            if update['Funktion'] == 'auto':
                self.Automatisch = not self.Automatisch
                self.resume()
            else:
                self.Automatisch = False
            if update['Funktion'] == 'greifen':
                ort = int(update['Info'])
                if 0 <= ort < len(self.Route)+1:
                    self.Manuell_greifen = ort
                    self.resume()
            elif update['Funktion'] == 'platzieren':
                ort = int(update['Info'])
                if 0 <= ort < len(self.Route)+1:
                    self.Manuell_platzieren = ort
                    self.resume()
            elif update['Funktion'] in 'bewegeGelenk+':
                self.Gelenkwerte = [int(wert) for wert in literal_eval(update['Info'])]
                if update['Funktion'] == 'bewegeGelenk+':
                    self.Relativ = True
                else:
                    self.Relativ = False
                self.resume()
                
    def OnRun(self):
        while True:
            self.suspend()
            if self.Automatisch:
                self.auto_ablauf()
            if self.Gelenkwerte:
                g1, g2, g3, g4, g5, g6 = self.Gelenkwerte
                self.Roboter.driveJoints(g1, g2, g3, g4, g5, g6, 0, self.Relativ)
                self.Gelenkwerte = None
            if self.Manuell_greifen:
                self.greife_komponente(self.Manuell_greifen-1)
                if self.Komponente_im_greifer:
                    self.Manuell_greifen = 0
            elif self.Manuell_platzieren:
                self.platziere_komponente(self.Manuell_platzieren-1)
                if not self.Komponente_im_greifer:
                    self.Manuell_platzieren = 0


    def auto_ablauf(self):
        for i in self.Route_range:
            if not self.Automatisch:
                break
            next_komponente = self.Komponenten_auf_route[i+1]
            if next_komponente:
                continue
            self.greife_komponente(i)
            self.platziere_komponente(i)


    def add_buffer(self, bool_wert):
        if self.Produktzustand.Value == 'ruhend' and bool_wert:
            self.Buffer.append(self.Komponenten_sensor.Value)
        elif self.Produktzustand.Value == 'bewegend':
            self.Buffer = [self.Komponenten_sensor.Value]

        
    def check_start(self):
        if self.Automatisch or self.Manuell_greifen == 1:
            if not self.Komponenten_auf_route[0] and self.Buffer:
                self.Komponenten_auf_route[0] = self.Buffer.pop(0)
        if self.Automatisch and self.Komponenten_auf_route[0] and not self.Komponenten_auf_route[1]:
            self.resume()
        elif self.Manuell_greifen == 1:
            self.resume()
        

    def ermittle_maschinen(self):
        self.Maschinen = []
        maschinen = [route['Container'] for route in self.Route if route['Typ'] == 'Maschine']
        port_start = 300
        for maschine in maschinen:
            fertig = maschine.getProperty('Schnittstelle::Fertig')
            offen = maschine.findBehaviour('TO_PLC_DoorIsOpen')
            auf = maschine.findBehaviour('FROM_PLC_OpenDoor')
            zu = maschine.findBehaviour('FROM_PLC_CloseDoor')
            start = maschine.findBehaviour('FROM_PLC_StartProcess')
            port = port_start
            port_start += 1
            iMaschine ={'Maschine': maschine, 'Offen':offen, 'Zu':zu, 'Start':start,'Auf':auf,'Port':port, 'Fertig':fertig}
            self.Maschinen.append(iMaschine)

    def ermittle_route(self):
        self.Route = []
        self.Route_ports = [port for port in self.Signal_input.getAllConnectedPorts() if 150 <= port < 200]
        for port in self.Route_ports:
            komp_container = self.Signal_input.getConnectedExternalSignals(port)[0].Component
            typ = komp_container.getProperty('Schnittstelle::Typ').Value
            route = {'Container':komp_container,'Typ': typ,'Port': port}
            self.Route.append(route)

    def greife_komponente(self, index):
        iRoute = self.Route[index]
        komponente = self.Komponenten_auf_route[index]
        komp_container = iRoute['Container']
        typ = iRoute['Typ']
        if komponente and not self.Komponente_im_greifer:
            if typ == 'Transport':
                self.Roboter.pickMovingPart(komponente)
                self.Komponente_im_greifer = komponente
                self.Komponenten_auf_route[index] = None
                self.check_start()
            elif typ == 'Maschine':
                offen, fertig = [(iMaschine['Offen'],iMaschine['Fertig'])  for iMaschine in self.Maschinen if iMaschine['Maschine']==komp_container][0]
                if self.Automatisch and not fertig.Value:
                    return
                if offen.Value:
                    self.zu_maschine(komp_container, komponente, 'greifen')
                    self.Komponente_im_greifer = komponente
                    self.Komponenten_auf_route[index] = None
                    self.check_start()
            self.Roboter.driveJoints(0,0,90,0,0,0)
    
    def konfiguriere_komponente(self, vcscript):
        script = self.Komponente.findBehaviour('Script')
        if not self.Komponente.findBehaviour('UpdateSignal'):
            self.Update_signal = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
            self.Update_signal.Connections = [script]
        
        if not self.Komponente.getProperty('Schnittstelle::Typ'):
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP

        if not self.Produktzustand:
            self.Produktzustand = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Produktzustand', vcscript.VC_PROPERTY_STEP)
            self.Produktzustand.StepValues = ['ruhend', 'bewegend']
        

    def platziere_komponente(self, index):
        if self.Automatisch:
            index += 1
        iRoute = self.Route[index]
        next_komponente = self.Komponenten_auf_route[index]
        komponente = self.Komponente_im_greifer
        komp_container = iRoute['Container']
        typ = iRoute['Typ']
        if not next_komponente and komponente:
            if typ == 'Transport':
                self.Roboter.place(komp_container)
                self.Komponente_im_greifer = None
            elif typ == 'Maschine':
                offen = [iMaschine['Offen'] for iMaschine in self.Maschinen if iMaschine['Maschine']==komp_container][0]
                if offen.Value:
                    self.zu_maschine(komp_container, komponente, 'platzieren')
                    self.Komponenten_auf_route[index] = komponente
                    self.Komponente_im_greifer = None
            self.Roboter.driveJoints(0,0,90,0,0,0)
    
    def zu_maschine(self, komp_container, komponente, anfahrt):
        self.Roboter.jointMoveToComponent(komp_container, ToFrame = 'ProductLocationApproach')
        self.Roboter.jointMoveToComponent(komp_container, Rx=-90, Ty=komponente.BoundCenter.length() * 2, ToFrame='ResourceLocation')
        if anfahrt == 'greifen':
            self.Roboter.graspComponent(komponente)
        elif anfahrt == 'platzieren':
            self.Roboter.releaseComponent(komp_container)



    def verwalte_signale(self, signal_map, port, bool_wert):
        if port == 150 and bool_wert:
            self.add_buffer(bool_wert)
            self.check_start()
        elif port in self.Route_ports and bool_wert:
            self.resume()

                    

            

   