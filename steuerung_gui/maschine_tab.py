#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from komponenten.datenbank import Datenbank

class MaschineTab:
    def __init__(self, steuerung,):
        self.TYP = 'Maschine'

        self.Steuerung = steuerung
        self.Tab_maschine = ttk.Frame(steuerung.Tab_parent)
        self.Maschine_auswahl = tk.StringVar()
        self.Maschine_komponenten = sorted([name for name, typ in self.Steuerung.Komponenten if typ == self.TYP])
        self.Vcmd = (self.Tab_maschine.register(self.OnValidierung), '%P')

        if not self.Maschine_komponenten:
            self.Maschine_komponenten = ['None']

        steuerung.Tab_parent.add(self.Tab_maschine, text = self.TYP)
        self.maschineauswahl()
        self.funktion_automatisch()
        self.funktion_auf_start_zu()

    def maschineauswahl(self):
        self.Maschine_auswahl.set(self.Maschine_komponenten[0])
        
        frame_auswahl = tk.Frame(self.Tab_maschine)
        frame_auswahl.grid(row=0, padx=(10,0), pady=(10, 5), sticky='W')

        maschineliste = tk.OptionMenu(frame_auswahl, self.Maschine_auswahl, *self.Maschine_komponenten)
        self.Steuerung.platziere_widget(maschineliste)
    
    def funktion_automatisch(self):
        prozesszeit = tk.StringVar()
        prozesszeit.set('1')

        frame_auto = tk.Frame(self.Tab_maschine)
        frame_auto.grid(row=1, padx=(10,0), pady=(5,5), sticky='W')

        entry_zeit = tk.Entry(frame_auto, takefocus=0, textvariable=prozesszeit, validate='key', validatecommand=self.Vcmd)
        
        cmd_einstellen = lambda: self.Steuerung.update_datenbank(self.Maschine_auswahl.get(), self.TYP, 'zeit', prozesszeit.get() or '0')
        button_einstellen = tk.Button(frame_auto, text='Einstellen', takefocus=0, command=cmd_einstellen)

        cmd_auto = lambda: self.Steuerung.update_datenbank(self.Maschine_auswahl.get(), self.TYP, 'auto', '')
        button_auto = tk.Button(frame_auto, text='Automatisch', takefocus=0, command=cmd_auto)

        widgets_auto = ((entry_zeit, 3),(button_einstellen,12), (button_auto, 12))
        for widget, breite in widgets_auto:
            self.Steuerung.platziere_widget(widget, breite)
    
    def funktion_auf_start_zu(self):
        fram_asz = tk.Frame(self.Tab_maschine)
        fram_asz.grid(row=2, padx=(10,0), pady=(5,5), sticky='W')

        cmd_auf = lambda: self.Steuerung.update_datenbank(self.Maschine_auswahl.get(), self.TYP, 'auf', '')
        button_auf = tk.Button(fram_asz, text='Auf', takefocus=0, command=cmd_auf)

        cmd_start = lambda: self.Steuerung.update_datenbank(self.Maschine_auswahl.get(), self.TYP, 'start', '')
        button_start = tk.Button(fram_asz, text='Start', takefocus=0, command=cmd_start)

        cmd_zu = lambda: self.Steuerung.update_datenbank(self.Maschine_auswahl.get(), self.TYP, 'zu', '')
        button_zu = tk.Button(fram_asz, text='Zu', takefocus=0, command=cmd_zu)

        widgets_asz = ((button_auf, 12), (button_start, 12), (button_zu, 12))

        for widget, breite in widgets_asz:
            self.Steuerung.platziere_widget(widget, breite)


    def OnValidierung(self, entry_wert):
        if entry_wert=='' or entry_wert.isdigit():
            return True
        else:
            return False