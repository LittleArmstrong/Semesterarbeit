#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .datenbank import Datenbank
from ast import literal_eval
import os
import konstanten

class Schnittstelle():
    # __init__ und exklusive Funktionen
    def __init__(self, vcscript):
        # Datenbank-Konstanten
        # - DATENBANK_REAL: enthält Befehle an reale Anlage
        # - DATENBANK_VIRTUELL: enthält Befehle an virtuelle Anlage
        # - DATENBANK_KOMPONENTEN: enthält die Namen der Komponenten in der realen Anlage. Notwendig für die Steuerung zum Senden der Befehle
        self.PFAD_DATENBANK_REAL = konstanten.PFAD_SIGNALE_REAL
        self.PFAD_DATENBANK_VIRTUELL = konstanten.PFAD_SIGNALE_VIRTUELL
        self.PFAD_DATENBANK_KOMPONENTEN = konstanten.PFAD_KOMPONENTEN
        # - Tabellenname der virtuellen und realen Datenbanken
        self.TABELLE_DATENBANK_SIGNALE = konstanten.TABELLE_SIGNALE
        # - Tabellenname der Komponenten-Datenbank
        self.TABELLE_DATENBANK_KOMPONENTEN = konstanten.TABELLE_KOMPONENTEN
        self.DATENBANK_PFADE_MIT_TABELLEN = [(self.PFAD_DATENBANK_REAL, self.TABELLE_DATENBANK_SIGNALE), \
            (self.PFAD_DATENBANK_VIRTUELL, self.TABELLE_DATENBANK_SIGNALE),\
            (self.PFAD_DATENBANK_KOMPONENTEN, self.TABELLE_DATENBANK_KOMPONENTEN)]
        # Referenz zur Anwendung
        self.App = vcscript.getApplication()
        # Referenz zur Komponente
        self.Komponente = vcscript.getComponent()
        self.Komponente.Name = 'Schnittstelle'
        # Erstelle notwendige Eigenschaften und Behaviours
        self.konfiguriere_komponente(vcscript)
        # Erstelle Tabelle, falls Datenbank neu erstellt wurde
        self.konfiguriere_datenbanken()
        # Importierte Funktionen
        self.delay = vcscript.delay
    
    def konfiguriere_datenbanken(self):
        # Gehe die Pfade durch: Ist die Datenbank leer bzw. existiert keine, so erstelle eine und füge dieser eine Tabelle hinzu
        for pfad, tabelle in self.DATENBANK_PFADE_MIT_TABELLEN:
            if Datenbank(pfad) and  os.stat(pfad).st_size != 0:
                continue
            felder_mit_typen = None
            if tabelle == 'Signale':
                felder_mit_typen = ('Name STRING PRIMARY KEY', 'Typ STRING NOT NULL', 'Funktion STRING', 'Info STRING')
            elif tabelle == 'Komponenten':
                felder_mit_typen = ('Name STRING PRIMARY KEY', 'Typ STRING NOT NULL')
            # Erstelle Datenbank mit Tabelle
            if felder_mit_typen:
                db = Datenbank(pfad)
                db.create_query(tabelle, felder_mit_typen)

    def konfiguriere_komponente(self, vcscript):
        # Eigenschaft
        if not self.Komponente.getProperty('Schnittstelle::Anlage'):
            self.Anlage = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Anlage', vcscript.VC_PROPERTY_STEP)
            self.Anlage.StepValues = ['real', 'virtuell']
            self.Anlage.Value = 'real'

    # OnStart-Event und exklusive Funktionen
    def OnStart(self):
        # Eigenschaften des Objekts  
        self.Alle_komponenten = {komponente.Name : komponente for komponente in self.App.Components}
        # - Gibt an, ob es sich hier um eine reale oder virtuelle Anlage handelt
        self.Anlage = self.Komponente.getProperty('Schnittstelle::Anlage').Value
        # Lösche alle Einträge in den Datenbanken und aktualisiere die Komponenten-Datenbank
        if self.Anlage == 'real':
            self.reset_alle_datenbanken()
            self.update_komponenten_datenbank()

    def reset_alle_datenbanken(self):
        # Lösche alle Einträge in den Tabellen aller Datenbanken
        for pfad, tabelle in self.DATENBANK_PFADE_MIT_TABELLEN:
            db = Datenbank(pfad)
            db.delete_query(tabelle)
    
    def update_komponenten_datenbank(self):
        # Aktualisiere die Komponenten Datenbank mit den Namen der Komponenten
        db = Datenbank(self.PFAD_DATENBANK_KOMPONENTEN)
        for name, komponente in self.Alle_komponenten.items():
            typ = komponente.getProperty('Schnittstelle::Typ')
            if typ and typ.Value:
                parameter = (name, typ.Value)
                db.replace_query(self.TABELLE_DATENBANK_KOMPONENTEN, parameter)
        
    def OnSignal(self, signal):
        pass

    # OnRun-Event und exklusive Funktionen    
    def OnRun(self):
        db, delay_zeit = self.check_anlage()
        tabelle = self.TABELLE_DATENBANK_SIGNALE
        # Gehe alle Datenbankzeilen durch
        while True:
            db_zeile = {}
            update_db = []
            for zeile in db.get_all_data(tabelle, sofort = False):
                db_zeile['Name'], db_zeile['Typ'], db_zeile['Funktion'], db_zeile['Info'] = zeile
                if db_zeile['Funktion']:
                    self.update_komponente(db_zeile)
                    self.reset_zeile(update_db, db_zeile)
            # Resette die gelesenen Zeilen am Ende
            for zeile in update_db:
                db.replace_query(tabelle, zeile)
            self.delay(delay_zeit)
    
    def check_anlage(self):
        # Delay-Zeiten wurden willkürlich gewählt, aber die der virtuellen sollte kleiner als die der realen sein
        # Falls nicht virtuell, wird automatisch real angenommen
        db = Datenbank(self.PFAD_DATENBANK_REAL)
        delay_zeit = 0.1
        if self.Anlage == 'virtuell':
            db = Datenbank(self.PFAD_DATENBANK_VIRTUELL)
            delay_zeit = 0.05
        return db, delay_zeit

    def reset_zeile(self, liste, zeile):
        # Funktion und Info werden nachdem lesen gelöscht
        db_zeile = [zeile['Name'], zeile['Typ'], '', '']
        liste.append(db_zeile)

    def update_komponente(self, db_zeile):
        # Update-Informationen werden an die jeweilige Komponente weitergereicht
        signal_wert = repr({key:db_zeile[key] for key in ('Funktion', 'Info')})
        komponente = self.Alle_komponenten[db_zeile['Name']]
        signal = komponente.getBehaviour('UpdateSignal')
        signal.signal(signal_wert)
    

    

    

    
    

    

    
    


    


    
