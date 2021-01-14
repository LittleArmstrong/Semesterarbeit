#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from komponenten.datenbank import Datenbank


class TransportTab():
    def __init__(self, steuerung):
        self.TYP = 'Transport'

        self.Steuerung = steuerung
        self.Tab_transport = ttk.Frame(steuerung.Tab_parent)
        self.Transport_auswahl = tk.StringVar()
        self.Transport_komponenten = sorted([name for name, typ in self.Steuerung.Komponenten if typ == self.TYP])

        if not self.Transport_komponenten:
            self.Transport_komponenten = ['None']

        steuerung.Tab_parent.add(self.Tab_transport, text='Transport')
        self.transportauswahl()
        self.funktion_komponente_umleiten()
    

    def transportauswahl(self):
        self.Transport_auswahl.set(self.Transport_komponenten[0])

        frame_auswahl = tk.Frame(self.Tab_transport)
        frame_auswahl.grid(row=0, padx=(10,0), pady=(10, 5), sticky='W')

        transportliste = tk.OptionMenu(frame_auswahl, self.Transport_auswahl, *self.Transport_komponenten)
        self.Steuerung.platziere_widget(transportliste)


    def funktion_komponente_umleiten(self):
        zu_komponente = tk.StringVar()
        zu_komponente.set(self.Transport_komponenten[1])

        frame_ku = tk.Frame(self.Tab_transport)
        frame_ku.grid(row=1, padx=(10,0), pady=(5,5), sticky='W') 

        auswahl_komponente = tk.OptionMenu(frame_ku, zu_komponente, *self.Transport_komponenten)
        
        cmd = lambda: self.Steuerung.update_datenbank(self.Transport_auswahl.get(), self.TYP, 'umleiten', zu_komponente.get())
        button_umleiten = tk.Button(frame_ku, text='Umleiten', command = cmd, takefocus=0)

        widgets_ku = ((auswahl_komponente, None), (button_umleiten, 12))
        for widget, breite in widgets_ku:
            self.Steuerung.platziere_widget(widget, breite)
