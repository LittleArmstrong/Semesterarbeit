#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .datenbank import Datenbank
from ast import literal_eval
import konstanten

class Maschine():
    def __init__(self, vcscript):
        # Konstanten
        self.TYP = 'Maschine'

        self.Komponente = vcscript.getComponent()


        self.Auf = self.Komponente.findBehaviour('FROM_PLC_OpenDoor')
        self.Ist_auf = self.Komponente.findBehaviour('TO_PLC_DoorIsOpen')
        self.Ist_busy = self.Komponente.findBehaviour('TO_PLC_ProcessIsRunning')
        self.Ist_zu = self.Komponente.findBehaviour('TO_PLC_DoorIsClosed')
        self.Start = self.Komponente.findBehaviour('FROM_PLC_StartProcess')
        self.Belegt = self.Komponente.findBehaviour('TransSignal') 
        self.Zu = self.Komponente.findBehaviour('FROM_PLC_CloseDoor')

        self.Fertig = self.Komponente.getProperty('Schnittstelle::Fertig')
        self.Prozesszeit = self.Komponente.getProperty('ProcessTime')
        
        self.konfiguriere_komponente(vcscript)

        self.Steuerung = 'automatisch'

        self.resume = vcscript.resumeRun
        self.suspend = vcscript.suspendRun

    def OnSignal(self, signal):
        if signal.Name == 'UpdateSignal':
            update = literal_eval(signal.Value) 
            if update['Funktion'] == 'auto':
                if self.Steuerung == 'automatisch':
                    self.Steuerung = 'manuell'
                else:
                    self.Steuerung = 'automatisch'
                    self.resume()
            else:
                self.Steuerung = 'manuell'
            if update['Funktion'] == 'zeit':
                zeit = int(update['Info'])
                if zeit:
                    self.Prozesszeit.Value = zeit
            if update['Funktion'] == 'auf':
                self.Auf.signal(True)
            elif update['Funktion'] == 'zu':
                self.Zu.signal(True)
            elif update['Funktion'] == 'start':
                prozesszeit = int(update['Info'])
                if prozesszeit:
                    self.Prozesszeit.Value = prozesszeit
                self.Start.signal(True)
        elif signal == self.Belegt:
            if signal.Value:
                self.Fertig.Value = 0
                self.resume()
        elif signal == self.Ist_busy:
            if not self.Ist_busy.Value:
                self.Fertig.Value = 1
                self.resume()
        
    def OnStart(self):
        self.Ist_auf.signal(True)
        self.Steuerung = 'automatisch'
        self.Fertig.Value = 0

    def OnRun(self):
        while True:
            self.suspend()
            if self.Steuerung == 'automatisch':
                if self.Ist_auf and not self.Fertig.Value:
                    self.Auf.signal(False)
                    self.Zu.signal(True)
                    self.Start.signal(True)
                elif self.Ist_zu and self.Fertig.Value:
                    self.Zu.signal(False)
                    self.Start.signal(False)
                    self.Auf.signal(True)

    def konfiguriere_komponente(self, vcscript):
        script = self.Komponente.findBehaviour('Script')
        if not self.Komponente.findBehaviour('UpdateSignal'):
            self.Update_signal = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
            self.Update_signal.Connections = [script]
        
        if not self.Fertig:
            self.Fertig = self.Komponente.createProperty(vcscript.VC_REAL, 'Schnittstelle::Fertig')

        self.Ist_auf.Connections += [script]
        self.Ist_busy.Connections += [script]
        self.Ist_zu.Connections += [script]
        self.Belegt.Connections += [script]