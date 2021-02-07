#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
from komponenten.datenbank import Datenbank


class RoboterTab:
    """Erstellt den Reiter Roboter samt Inhalt und stellt die Funktionen bereit.
    
    Attribute
    - - - - - 
    TYP - str
        zum Erkennen der Komponenten für die die Funktionen bestimmt sind
    Steuerung - Steuerung
        Referenz zum Steuerung-Objekt
    Tab_Roboter - Frame
        die Frame, in dem die Elemente platziert werden
    Roboter_komponenten - list
        alle Komponenten im Layout mit dem Typ Roboter
    Roboter_auswahl - StringVar
        speichert die ausgewählte Komponente zu der die Informationen gesendet werden sollen
    Vcmd - vcmd
        zum Abfangen von eingegebenen Werten
    """

    def __init__(self, steuerung):
        """Eine Zeile = eine Funktion. Platziere die ganzen Funktionen.

        Parameter
        - - - - -
        steuerung - Steuerung
            um Zugriff zu den Komponentennamen und Funktionen zu erhalten
        """
        self.TYP = 'Roboter'

        self.Steuerung = steuerung
        self.Tab_roboter = ttk.Frame(steuerung.Tab_parent)
        self.Roboter_komponenten = sorted([name for name, typ in self.Steuerung.Komponenten if typ == self.TYP])
        self.Roboter_auswahl = tk.StringVar()
        self.Vcmd = (self.Tab_roboter.register(self.OnValidierung), '%P')

        if not self.Roboter_komponenten:
            self.Roboter_komponenten = ['None']

        steuerung.Tab_parent.add(self.Tab_roboter, text = self.TYP)
        self.roboterauswahl()
        self.funktion_automatisch_greifen_platzieren()
        self.funktion_bewege_gelenke()
    
    
    def roboterauswahl(self):
        """Platziert eine Auswahlliste mit den Komponentennamen.
        """
        self.Roboter_auswahl.set(self.Roboter_komponenten[0])
        
        frame_auswahl = tk.Frame(self.Tab_roboter)
        frame_auswahl.grid(row=0, padx=(10,0), pady=(10, 5), sticky='W')

        roboterliste = tk.OptionMenu(frame_auswahl, self.Roboter_auswahl, *self.Roboter_komponenten)
        self.Steuerung.platziere_widget(roboterliste)
    
    
    def funktion_automatisch_greifen_platzieren(self):
        """ Schaltfläche zum Wechseln zwischen Automatisch und Manuell.

        Textfeld und Schaltfläche, um die Station auszuwählen an der die beabsichtigte Bewegung (greifen oder platzieren) 
        durchgeführt werden soll.
        """

        greifstelle = tk.StringVar()
        platzierstelle = tk.StringVar() 
        
        greifstelle.set('1')
        platzierstelle.set('1')

        frame_agp = tk.Frame(self.Tab_roboter)
        frame_agp.grid(row=1, padx=(10,0), pady=(5,5), sticky='W')

        cmd_automatisch = lambda: self.Steuerung.update_datenbank(self.Roboter_auswahl.get(), self.TYP, 'auto', '')
        button_automatisch = tk.Button(frame_agp, text='Automatisch', takefocus=0, command=cmd_automatisch)

        entry_greifstelle = tk.Entry(frame_agp, takefocus=0, textvariable=greifstelle, validate='key', validatecommand=self.Vcmd)
        cmd_greifen = lambda: self.Steuerung.update_datenbank(self.Roboter_auswahl.get(), self.TYP, 'greifen', greifstelle.get() or '0')
        button_greifen = tk.Button(frame_agp, text='Greifen', takefocus=0, command=cmd_greifen)

        entry_platzierstelle = tk.Entry(frame_agp, takefocus=0, textvariable=platzierstelle, validate='key', validatecommand=self.Vcmd)
        cmd_platzieren = lambda: self.Steuerung.update_datenbank(self.Roboter_auswahl.get(), self.TYP, 'platzieren', platzierstelle.get() or '0')
        button_platzieren = tk.Button(frame_agp, text='Platzieren', takefocus=0, command=cmd_platzieren)

        widgets_apg = ((button_automatisch, 12), (entry_greifstelle, 3), (button_greifen, 12),
         (entry_platzierstelle, 3), (button_platzieren, 12))
        for widget, breite in widgets_apg:
            self.Steuerung.platziere_widget(widget, breite)

    
    def cmd_bewegen(self, name, relativ, gelenk_werte):
        """Gibt den Befehl an den Roboter eine bestimmte Haltung einzunehmen.

        Parameter
        - - - - - 
        name - str
            Name der Komponente
        relativ - int
            ob es sich um relative oder absolute Gelenkwerte handelt
        gelenk_werte - list
            die Werte für die einzelnen Gelenke (6)
        """
        funktion = 'bewegeGelenk' + '+' * relativ
        info = repr(gelenk_werte)
        self.Steuerung.update_datenbank(name, self.TYP, funktion, info)


    def funktion_bewege_gelenke(self):
        """ Für jedes Gelenk ein Textfeld und eine Schaltfläche zum Absenden der Informationen an die Datenbank.
        """
        relativ = tk.IntVar()
        relativ.set(0)

        widgets_bg = []
        entries = []

        frame_bg = tk.Frame(self.Tab_roboter)
        frame_bg.grid(row=2, padx=(10,0), pady=(5,5), sticky='W')

        for _i in range(6):
            entry_var = tk.StringVar()
            entry_var.set('0')
            entry_gelenk = tk.Entry(frame_bg, takefocus=0, textvariable=entry_var, validate='key', validatecommand=self.Vcmd)
            entries.append(entry_var)
            widgets_bg.append((entry_gelenk, 3))

        checkbox_relativ = tk.Checkbutton(frame_bg, text='relativ', variable=relativ, takefocus=0)
        cmd_bewegen = lambda: self.cmd_bewegen(self.Roboter_auswahl.get(), relativ.get(),[entry.get() or '0' for entry in entries])
        button_bewegen = tk.Button(frame_bg, text='Bewegen', command=cmd_bewegen, takefocus=0)
        widgets_bg += [(checkbox_relativ, None), (button_bewegen, 12)]

        for widget, breite in widgets_bg:
            self.Steuerung.platziere_widget(widget, breite)
    
    def OnValidierung(self, entry_wert):
        """Nur Zahlen und Minuszeichen erlaubt.

        Parameter
        - - - - -
        entry_wert - str
            der eingegebene Wert, welches geprüft werden soll
        """
        if entry_wert=='' or entry_wert.isdigit() or entry_wert.startswith('-'):
            return True
        else:
            return False
    


