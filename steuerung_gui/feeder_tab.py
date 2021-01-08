#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from komponenten.datenbank import Datenbank

class FeederTab:
    def __init__(self, steuerung):
        self.TYP = 'Feeder'

        self.Steuerung = steuerung
        self.Tab_feeder = ttk.Frame(steuerung.Tab_parent)
        self.Feeder_komponenten = sorted([name for name, typ in self.Steuerung.Komponenten if typ == self.TYP])
        self.Feeder_auswahl = tk.StringVar()
        self.Vcmd = (self.Tab_feeder.register(self.OnValidierung), '%P')

        steuerung.Tab_parent.add(self.Tab_feeder, text = self.TYP)
        self.feederauswahl()
        self.funktion_erstelle()
        self.funktion_intervall()


    def feederauswahl(self):
        self.Feeder_auswahl.set(self.Feeder_komponenten[0])
        
        frame_auswahl = tk.Frame(self.Tab_feeder)
        frame_auswahl.grid(row=0, padx=(10,0), pady=(10, 5), sticky='W')

        feederliste = tk.OptionMenu(frame_auswahl, self.Feeder_auswahl, *self.Feeder_komponenten)
        self.Steuerung.platziere_widget(feederliste)
    

    def funktion_erstelle(self):
        frame_erstelle = tk.Frame(self.Tab_feeder)
        frame_erstelle.grid(row=1, padx=(10,0), pady=(5,5), sticky='W')

        cmd_erstelle = lambda: self.Steuerung.update_datenbank(self.Feeder_auswahl.get(), self.TYP, 'erstelle', '')
        button_erstelle = tk.Button(frame_erstelle, text='Erstellen', command= cmd_erstelle)
        
        widget = button_erstelle
        breite = 12
        self.Steuerung.platziere_widget(widget, breite)


    def funktion_intervall(self):
        sofort = tk.IntVar()
        intervall = tk.StringVar()

        sofort.set(1)
        intervall.set('0')

        frame_intervall = tk.Frame(self.Tab_feeder)
        frame_intervall.grid(row=2, padx=(10,0), pady=(5,5), sticky='W')

        entry_intervall = tk.Entry(frame_intervall, text='0', textvariable=intervall, validate='key', validatecommand=self.Vcmd)
        checkbox_sofort = tk.Checkbutton(frame_intervall, text='Sofort', variable=sofort)

        cmd_intervall = lambda: self.cmd_funktion_intervall(sofort.get(), self.Feeder_auswahl.get(), intervall.get())
        button_intervall = tk.Button(frame_intervall, text='Erstellen', command = cmd_intervall)

        widgets_eii = ((entry_intervall, 3), (checkbox_sofort, None), (button_intervall, 12))
        for widget, breite in widgets_eii:
            self.Steuerung.platziere_widget(widget, breite)


    def OnValidierung(self, entry_wert):
        if entry_wert.isdigit() or entry_wert == '':
            return True
        else:
            return False

    def cmd_funktion_intervall(self, checkbox, komponente, intervall):
        funktion = 'intervall'
        if checkbox:
            funktion = 'intervall_sofort'
        self.Steuerung.update_datenbank(komponente, self.TYP, funktion, intervall or '0')

