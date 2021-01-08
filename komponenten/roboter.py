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

        self.konfiguriere_komponente(vcscript)
        
        self.Buffer = []
        self.Roboter = None
        self.Komponente_im_greifer = None
        self.Komponenten_auf_route = []
        self.Komponenten_sensor = None
        self.Maschinen = []
        self.Maschinen_ports = []
        self.Route = []
        self.Route_ports = []
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
        self.verbinde_mit_maschinen()
        self.reset_maschinen_signale()

        self.Buffer = []
        self.Komponenten_auf_route = [None for komp in self.Route]
        self.Komponente_im_greifer = None

    def OnSignal(self, signal):
        if signal.Name == 'UpdateSignal':
            update = literal_eval(signal.Value) 
            if update['Funktion'] == 'auto':
                pass

    def OnRun(self):
        while True:
            self.suspend()
            for i in range(len(self.Komponenten_auf_route) -2, -1, -1):
                komponente = self.Komponenten_auf_route[i]
                if not komponente:
                    continue
                typ = self.Route[i][1]
                if typ == 'Maschine':
                    maschine = self.Route[i][0]
                    offen_signal = [maschinen_info[1] for maschinen_info in self.Maschinen if maschinen_info[0] == maschine][0]
                    aufmachen_signal = [maschinen_info[3] for maschinen_info in self.Maschinen if maschinen_info[0] == maschine][0]
                next_komponente = self.Komponenten_auf_route[i+1]
                if komponente and not next_komponente:
                    if typ == 'Maschine' and not offen_signal.Value:
                        aufmachen_signal.signal(True)
                    self.greife_komponente(i, komponente)
                    self.platziere_komponente(i)
        
    def check_routen_start(self):
        if not self.Komponenten_auf_route[0] and self.Buffer:
            self.Komponenten_auf_route[0] = self.Buffer.pop(0)
        if self.Komponenten_auf_route[0] and not self.Komponenten_auf_route[1]:
            self.resume()

    def ermittle_maschinen(self):
        self.Maschinen = []
        self.Maschinen_ports = []
        maschinen = [route[0] for route in self.Route if route[1] == 'Maschine']
        maschinen_port_start = 300
        for maschine in maschinen:
            offen_signal = maschine.findBehaviour('TO_PLC_DoorIsOpen')
            aufmachen_signal = maschine.findBehaviour('FROM_PLC_OpenDoor')
            zumachen_signal = maschine.findBehaviour('FROM_PLC_CloseDoor')
            starten_signal = maschine.findBehaviour('FROM_PLC_StartProcess')
            maschinen_port = maschinen_port_start
            maschinen_port_start += 1
            maschinen_info = (maschine, offen_signal, zumachen_signal, starten_signal, aufmachen_signal, maschinen_port)
            self.Maschinen.append(maschinen_info)
            self.Maschinen_ports.append(maschinen_port)

    def ermittle_route(self):
        self.Route = []
        self.Route_ports = [port for port in self.Signal_input.getAllConnectedPorts() if 150 <= port < 200]
        for port in self.Route_ports:
            komponenten_container = self.Signal_input.getConnectedExternalSignals(port)[0].Component
            typ = komponenten_container.getProperty('Schnittstelle::Typ').Value
            route = (komponenten_container, typ, port)
            self.Route.append(route)

    def greife_komponente(self, index, komponente):
        route = self.Route[index]
        komponenten_container = route[0]
        typ = route[1]
        if typ == 'Transport' and not self.Komponente_im_greifer:
            self.Roboter.pickMovingPart(komponente)
            self.Komponente_im_greifer = komponente
            self.Komponenten_auf_route[index] = None
            self.check_routen_start()
        elif typ == 'Maschine' and not self.Komponente_im_greifer:
            self.Roboter.jointMoveToComponent(komponenten_container, ToFrame = 'ProductLocationApproach')
            self.Roboter.jointMoveToComponent(komponenten_container, Rx=-90, Ty=komponente.BoundCenter.length() * 2, ToFrame='ResourceLocation')
            self.Roboter.graspComponent(komponente)
            self.Komponente_im_greifer = komponente
            self.Komponenten_auf_route[index] = None
            self.check_routen_start()
        self.Roboter.driveJoints(0,0,90,0,0,0)
    
    def konfiguriere_komponente(self, vcscript):
        script = self.Komponente.findBehaviour('Script')
        if not self.Komponente.findBehaviour('UpdateSignal'):
            self.Update_signal = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
            self.Update_signal.Connections = [script]

        if not self.Komponente.getProperty('Schnittstelle::Typ'):
            typ = self.Komponente.createProperty(vcscript.String, 'Schnittstelle::Typ')
            typ.Value = self.TYP

    def platziere_komponente(self, index):
        route = self.Route[index + 1]
        komponente = self.Komponente_im_greifer
        komponenten_container = route[0]
        typ = route[1]
        if typ == 'Transport' and self.Komponente_im_greifer:
            self.Roboter.place(komponenten_container)
            self.Komponente_im_greifer = None
        elif typ == 'Maschine' and self.Komponente_im_greifer:
            self.Roboter.jointMoveToComponent(komponenten_container, ToFrame = 'ProductLocationApproach')
            self.Roboter.jointMoveToComponent(komponenten_container, Rx=-90, Ty=komponente.BoundCenter.length() * 2, ToFrame='ResourceLocation')
            self.Roboter.releaseComponent(komponenten_container)
            self.Komponenten_auf_route[index+1] = komponente
            self.Komponente_im_greifer = None
            self.steuere_maschine('start', maschine=komponenten_container)
        self.Roboter.driveJoints(0,0,90,0,0,0)

    def reset_maschinen_signale(self):
        for maschine in self.Maschinen:
            offen_signal = maschine[1]
            if not offen_signal.Value:
                offen_signal.signal(True)

    def steuere_maschine(self, zustand, maschine, port = None):
        for maschinen_info in self.Maschinen:
            if maschine == maschinen_info[0] or port == maschinen_info[5]:
                zumachen_signal = maschinen_info[2]
                prozess_signal = maschinen_info[3]
                aufmachen_signal = maschinen_info[4]
                if zustand == 'start':
                    aufmachen_signal.signal(False)
                    zumachen_signal.signal(True)
                    prozess_signal.signal(True)
                elif zustand == 'ende':
                    prozess_signal.signal(False)
                    zumachen_signal.signal(False)
                    aufmachen_signal.signal(True)
            
    def verbinde_mit_maschinen(self):
        maschine_mit_port = [(maschine[0], maschine[5]) for maschine in self.Maschinen]
        for maschine, port in maschine_mit_port:
            prozess_signal = maschine.findBehaviour('TO_PLC_ProcessIsRunning')
            self.Signal_input.connect(port, prozess_signal)

    def verwalte_signale(self, signal_map, port, bool_wert):
        if port == 150 and bool_wert:
            self.Buffer.append(self.Komponenten_sensor.Value)
            self.check_routen_start()
        elif port in self.Route_ports[1:-1] and bool_wert:
            self.resume()
        elif port in self.Maschinen_ports and not bool_wert:
                self.steuere_maschine('ende', maschine=None, port=port)
                    

            

   