#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from komponenten.datenbank import Datenbank
import konstanten

class TransportTab():

    def __init__(self, tab_parent, komponenten_mit_typ_transport):
        self.TYP = 'Transport'
        self.DB_PFAD = konstanten.PFAD_SIGNALE_REAL
        self.DB_TABELLE = konstanten.TABELLE_SIGNALE

        komponenten_mit_typ_transport.sort()
        self.main(tab_parent, komponenten_mit_typ_transport)

    def main(self, tab_parent, komponenten_mit_typ_transport):
        tab_transport = ttk.Frame(tab_parent)
        tab_parent.add(tab_transport, text='Transport')

        self.funktion_komponente_umleiten(tab_transport, komponenten_mit_typ_transport)
    
    def funktion_komponente_umleiten(self, tab_transport, komponenten_mit_typ_transport):
        var_komponente_typ_transport_von = tk.StringVar()
        var_komponente_typ_transport_von.set(komponenten_mit_typ_transport[0])
        var_komponente_typ_transport_zu = tk.StringVar()
        var_komponente_typ_transport_zu.set(komponenten_mit_typ_transport[0])

        label_von = tk.Label(tab_transport, text = 'Von')
        label_von.grid(row=0, column=0, padx=10, pady=10, sticky='W')

        auswahl_komponente_typ_transport_von = tk.OptionMenu(tab_transport, var_komponente_typ_transport_von, *komponenten_mit_typ_transport)
        auswahl_komponente_typ_transport_von.grid(row=0, column=1, padx=0, pady=10, sticky='W')

        label_zu = tk.Label(tab_transport, text = 'zu')
        label_zu.grid(row=0, column=2, padx=5, pady=10, sticky='W')

        auswahl_komponente_typ_transport_zu = tk.OptionMenu(tab_transport, var_komponente_typ_transport_zu, *komponenten_mit_typ_transport)
        auswahl_komponente_typ_transport_zu.grid(row=0, column=3, padx=0, pady=10, sticky='W')

        command = lambda: self.cmd_funktion_umleiten(var_komponente_typ_transport_von.get(), var_komponente_typ_transport_zu.get())
        umleite_button = tk.Button(tab_transport, text='Umleiten', command = command)
        umleite_button.config(width=12)
        umleite_button.grid(row=0, column=4, padx=10, pady=10, sticky='W')
    
    def cmd_funktion_umleiten(self, von_komponente, zu_komponente):
        db = Datenbank(self.DB_PFAD)
        parameter = (von_komponente, self.TYP, 'umleiten', zu_komponente)
        db.replace_query(self.DB_TABELLE, parameter)

