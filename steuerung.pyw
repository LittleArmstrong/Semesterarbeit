#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from komponenten.datenbank import Datenbank
from steuerung_gui.feeder_tab import FeederTab
from steuerung_gui.transport_tab import TransportTab
from steuerung_gui.roboter_tab import RoboterTab
from steuerung_gui.maschine_tab import MaschineTab
import konstanten

class Steuerung:
    def __init__(self):
        self.DB_PFAD = konstanten.PFAD_SIGNALE_REAL
        self.DB_TABELLE = konstanten.TABELLE_SIGNALE

        # --- Fenster
        fenster = tk.Tk()
        fenster.title('Steuerung')
        fenster.geometry('400x150')

        self.Tab_parent = ttk.Notebook()

        # --- Komponentenauswahl
        db = Datenbank(konstanten.PFAD_KOMPONENTEN)
        cursor = db.get_all_data(konstanten.TABELLE_KOMPONENTEN, sofort = False)
        self.Komponenten = [(name, typ) for name, typ in cursor]

        # --- Tabs
        self.erstelle_tabs()
        
        self.Tab_parent.pack(expand=1, fill='both')
        fenster.mainloop()
        

    def erstelle_tabs(self):
        FeederTab(self)
        TransportTab(self)
        RoboterTab(self)
        MaschineTab(self)


    def platziere_widget(self, widget, width=None):
        if width:
            widget.config(width=width)
        widget.pack(side='left', padx=(0, 10))
    
    
    def update_datenbank(self, name, typ, funktion, info):
        db = Datenbank(self.DB_PFAD)
        parameter = (name, typ, funktion, info)
        db.replace_query(self.DB_TABELLE, parameter)

if __name__ == "__main__":
    Steuerung()