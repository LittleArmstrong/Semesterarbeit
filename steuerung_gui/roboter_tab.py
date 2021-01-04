#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from komponenten.datenbank import Datenbank
import konstanten

class RoboterTab:
    def __init__(self, tab_parent, komponenten_mit_typ_roboter):
        self.TYP = 'Roboter'
        self.DB_PFAD = konstanten.PFAD_SIGNALE_REAL
        self.DB_TABELLE = konstanten.TABELLE_SIGNALE

        komponenten_mit_typ_roboter.sort()
        self.main(tab_parent, komponenten_mit_typ_roboter)

    def main(self, tab_parent, komponenten_mit_typ_roboter):
        tab_roboter = ttk.Frame(tab_parent)
        tab_parent.add(tab_roboter, text = self.TYP)

        self.funktion_auswahl_automatik_manuell(tab_roboter, komponenten_mit_typ_roboter)
        self.funktion_greifen_platzieren(tab_roboter, komponenten_mit_typ_roboter)
        self.funktion_bewege_gelenke(tab_roboter, komponenten_mit_typ_roboter)
    

    def funktion_auswahl_automatik_manuell(self, tab_roboter, komponenten_mit_typ_roboter):
        # Variablen
        # - Für die Auswahlliste
        var_roboter_komponente = tk.StringVar()
        var_roboter_komponente.set(komponenten_mit_typ_roboter[0])

        auswahl_komponente_typ_roboter = tk.OptionMenu(tab_roboter, var_roboter_komponente, *komponenten_mit_typ_roboter)
        auswahl_komponente_typ_roboter.grid(row=0, column=0, padx=10, pady=10, sticky='SW')

        cmd_automatisch = lambda: self.cmd_auswahl_automatik_manuell(var_roboter_komponente.get())
        automatisch_button = tk.Button(tab_roboter, text='Automatisch', takefocus=0, command=cmd_automatisch)
        automatisch_button.config(width = 12)
        automatisch_button.grid(row=0, column=1, padx=0, pady=10)

    def cmd_auswahl_automatik_manuell(self, komp_name):
        db = Datenbank(self.DB_PFAD)
        parameter = (komp_name, self.TYP, 'auto', '')
        db.replace_query(self.DB_TABELLE, parameter)

    def funktion_greifen_platzieren(self, tab_roboter, komponenten_mit_typ_roboter):
        var_roboter_komponente = tk.StringVar()
        var_roboter_komponente.set(komponenten_mit_typ_roboter[0])

        auswahl_komponente_typ_roboter = tk.OptionMenu(tab_roboter, var_roboter_komponente, *komponenten_mit_typ_roboter)
        auswahl_komponente_typ_roboter.grid(row=1, column=0, padx=10, pady=0, sticky='W')

        cmd_greifen = lambda: self.cmd_greifen(var_roboter_komponente.get())
        greifen_button = tk.Button(tab_roboter, text='Greifen', takefocus=0, command=cmd_greifen)
        greifen_button.config(width = 12)
        greifen_button.grid(row=1, column=1, padx=0, pady=0)

        cmd_platzieren = lambda: self.cmd_platzieren(var_roboter_komponente.get())
        platzieren_button = tk.Button(tab_roboter, text='Platzieren', takefocus=0, command=cmd_platzieren)
        platzieren_button.config(width = 12)
        platzieren_button.grid(row=1, column=2, padx=10, pady=0, sticky='W')

    def cmd_greifen(self, komp_name):
        db = Datenbank(self.DB_PFAD)
        parameter = (komp_name, self.TYP, 'greifen', '')
        db.replace_query(self.DB_TABELLE, parameter)

    def cmd_platzieren(self, komp_name):
        db = Datenbank(self.DB_PFAD)
        parameter = (komp_name, self.TYP, 'platzieren', '')
        db.replace_query(self.DB_TABELLE, parameter)

    def funktion_bewege_gelenke(self, tab_roboter, komponenten_mit_typ_roboter):
        var_roboter_komponente = tk.StringVar()
        var_roboter_komponente.set(komponenten_mit_typ_roboter[0])

        var_checkbox_relativ = tk.IntVar()
        var_checkbox_relativ.set(0)

        var_entry_1 = tk.IntVar()
        var_entry_2 = tk.IntVar()
        var_entry_3 = tk.IntVar()
        var_entry_4 = tk.IntVar()
        var_entry_5 = tk.IntVar()
        var_entry_6 = tk.IntVar()

        auswahl_komponente_typ_roboter = tk.OptionMenu(tab_roboter, var_roboter_komponente, *komponenten_mit_typ_roboter)
        auswahl_komponente_typ_roboter.grid(row=2, column=0, padx=10, pady=10, sticky='SW')
        
        entry_frame = tk.Frame(tab_roboter)
        entry_frame.grid(row=2, column = 1, padx=0, pady=10, sticky='W')

        vcmd = (entry_frame.register(self.OnValidierung), '%P')
        entry_gelenk_1 = tk.Entry(entry_frame, textvariable=var_entry_1, validate='key', validatecommand=vcmd)
        entry_gelenk_1.config(width=3)
        entry_gelenk_1.grid(row=0, column=0, padx=0, pady=0, sticky='W')

        entry_gelenk_2 = tk.Entry(entry_frame, textvariable=var_entry_2, validate='key', validatecommand=vcmd)
        entry_gelenk_2.config(width=3)
        entry_gelenk_2.grid(row=0, column=1, padx=0, pady=0, sticky='W')

        entry_gelenk_3 = tk.Entry(entry_frame, textvariable=var_entry_3, validate='key', validatecommand=vcmd)
        entry_gelenk_3.config(width=3)
        entry_gelenk_3.grid(row=0, column=2, padx=0, pady=0, sticky='W')

        entry_gelenk_4 = tk.Entry(entry_frame, textvariable=var_entry_4, validate='key', validatecommand=vcmd)
        entry_gelenk_4.config(width=3)
        entry_gelenk_4.grid(row=0, column=3, padx=0, pady=0, sticky='W')

        entry_gelenk_5 = tk.Entry(entry_frame, textvariable=var_entry_5, validate='key', validatecommand=vcmd)
        entry_gelenk_5.config(width=3)
        entry_gelenk_5.grid(row=0, column=4, padx=0, pady=0, sticky='W')

        entry_gelenk_6 = tk.Entry(entry_frame, textvariable=var_entry_6, validate='key', validatecommand=vcmd)
        entry_gelenk_6.config(width=3)
        entry_gelenk_6.grid(row=0, column=5, padx=0, pady=0, sticky='W')
        
        button_frame = tk.Frame(tab_roboter)
        button_frame.grid(row=2, column=2, padx=0, pady=10)

        cmd_bewegen = lambda: self.cmd_bewegen(var_roboter_komponente.get(),var_checkbox_relativ.get(),\
            [var_entry_1.get(), var_entry_2.get(), var_entry_3.get(), var_entry_4.get(), var_entry_5.get(), var_entry_6.get()])

        relativ_checkbox = tk.Checkbutton(button_frame, text='relativ', variable=var_checkbox_relativ)
        relativ_checkbox.grid(row=0, column=0, padx=0, pady=0)

        bewegen_button = tk.Button(button_frame, text='Bewegen', command=cmd_bewegen)
        bewegen_button.config(width=12)
        bewegen_button.grid(row=0, column=1, padx=0, pady=0)

    def cmd_bewegen(self, komp_name, relativ, gelenk_werte):
        db = Datenbank(self.DB_PFAD)
        funktion = 'bewegeGelenk' + '+' * relativ
        info = repr({'G' + str(i): wert for i, wert in enumerate(gelenk_werte, 1)})
        parameter = (komp_name, self.TYP, funktion, info)
        db.replace_query(self.DB_TABELLE, parameter)

    def OnValidierung(self, entry_wert):
        if entry_wert.isdigit() or entry_wert == '':
            return True
        else:
            return False

