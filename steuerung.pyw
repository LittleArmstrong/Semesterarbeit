#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from komponenten.datenbank import Datenbank
from steuerung_gui.feeder_tab import FeederTab
from steuerung_gui.transport_tab import TransportTab
from steuerung_gui.roboter_tab import RoboterTab
from steuerung_gui.maschine_tab import MaschineTab
import konst

class Steuerung:
    """GUI mit der die reale Anlage gesteuert wird. Es gibt für verschiedene Komponententypen verschiedene Funktionen.
    Vorhandene Reiter:
    - Feeder: zum Erstellen von Produkten
    - Transport: zum Umleiten der Produkte
    - Roboter: zum Steuern der Roboterbewegungen
    - Maschine: zum Steuern des Maschinenprozesses

    Methoden
    - - - - -
    erstelle_tabs() -> None
        erstellt und platziert den Reiter zusammen mit dem Inhalt
    platziere_widget(widget, breite=None) -> None
        platziert die Widget in bestimmtem Abstand und Größe
    update_datenbank(name, typ, funktion, info) -> None
        schreibt Informationen in die Datenbank für die reale Anlage
    """
    def __init__(self):
        """Erstelle Fenster, ermittle alle Komponenten im Layout und erstelle die Reiter samt Inhalt.
        """
        # --- Fenster
        fenster = tk.Tk()
        fenster.title('Steuerung')
        fenster.geometry('400x150')
        self.Tab_parent = ttk.Notebook()
        # --- Komponentenauswahl
        db = Datenbank(konst.PFAD_KOMP)
        cursor = db.get_all_data(konst.TABELLE_KOMP, sofort = False)
        self.Komponenten = [(name, typ) for name, typ in cursor]
        # --- Tabs
        self.erstelle_tabs()
        self.Tab_parent.pack(expand=1, fill='both')
        fenster.mainloop()

    def erstelle_tabs(self):
        """Instanzen der verschiedenen Tabs wird aufgerufen, die die Reiter und den inhalt erstellen und platzieren.
        """
        # Erstelle und fülle die Reiter für die jeweiligen Komp-Typen
        FeederTab(self)
        TransportTab(self)
        RoboterTab(self)
        MaschineTab(self)

    def platziere_widget(self, widget, breite=None):
        """Platziert widget in bestimmter Breite. Wird mit Frames zur einfachen Platzierung der Widgets nebeneinander genutzt.

        Parameter
        - - - - - 
        widget - widget
            das zu platzierende Widget
        breite=None - int, optional
            die Breite des Widget
        """
        # Platziere Widgets nebeneinander
        if breite:
            widget.config(width=breite)
        widget.pack(side='left', padx=(0, 10))
    
    def update_datenbank(self, name, typ, funktion, info):
        """
        Parameter
        - - - - -
        name - str
            Name der Komponente an die bestimmte Informationen gesendet werden sollen
        typ - str
            Typ der Komponente
        funktion - str
            die auszuführende Funktion der Komponente
        infor - str
            notwendige Informationen zur Ausführung der Funktion
        """
        # Informationen an Komps werden in Datenbank gespeichert
        db = Datenbank(konst.PFAD_R_SIGNALE)
        parameter = (name, typ, funktion, info)
        db.replace_query(konst.TABELLE_SIGNALE, parameter)

if __name__ == "__main__":
    Steuerung()