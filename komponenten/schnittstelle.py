#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .datenbank import Datenbank
import os
import konst

class Schnittstelle():
    """Klasse zum Lesen der Datenbanken und Weiterleiten der Informationen an die jeweiligen Komponenten. Irgendeine Komponente benutzen 
    oder erstellen und Pythonscript namens 'Script' hinzufügen:

    Scriptinhalt :
    import vcScript
    from vccode import Schnittstelle

    komptyp = Schnittstelle(vcScript)

    def OnStart():
        komptyp.OnStart()
    
    def OnSignal(signal):
        komptyp.OnSignal(signal)
    
    def OnRun():
        komptyp.OnRun()

    Attribute
    - - - - -
    Alle_komp - list of vcComponent
        alle Komponenten im Layout
    Anlage - str
        ob reale oder virtuelle Anlage
    App - vcApplication
        Referenz zur Anwendung
    
    Delay_zeit - int
        Zeit zwischen dem Lesen der Datenbank
    Pfad - str
        Pfad zur jeweiligen Datenbank (virtuell oder real)

    Importierte Funktion
    - - - - - - - - - - -
    delay(zeit) -> None
        stoppt die Ausführung des Scripts für bestimmte Zeit

    Methoden
    - - - - -
    OnStart() -> None
        Event - bestimmte alle Komponenten, die Delay_zeit und den Pfad
    OnSignal(signal) -> None
        nix
    OnRun() -> None
        liest alle Informationen in der Datenbank und signalisiert die jeweiligen Komponenten
    konfig_db() -> None
        erstellt Datenbank und Tabelle, falls nicht vorhanden
    konfig_komp(vcscript, komp) -> None
        erstellt die Eigenschaft 'Schnittstelle::Anlage'
    reset_alle_db() -> None
        Löscht alle Einträge in den Datenbanken
    update_komp(db_zeile) -> None
        signalisiert die jeweilige Komponente mit den Informationen aus der Datenbank
    update_komp_db() -> None
        aktualisiert die Datenbank für die Steuerung mit Komponentennamen und Typ 
    """
    def __init__(self, vcscript):
        """
        Parameter
        - - - - -
        vcscript - module
            Modul vcScript
        """
        # Konstante
        self.PFADE_TABELLEN = ((konst.PFAD_R_SIGNALE, konst.TABELLE_SIGNALE), (konst.PFAD_V_SIGNALE, konst.TABELLE_SIGNALE),\
                        (konst.PFAD_KOMP, konst.TABELLE_KOMP))
        komp = vcscript.getComponent()
        komp.Name = 'Schnittstelle'
        # Erstelle Eigenschaften/Verhaltensweisen falls notwendig
        self.konfig_komp(vcscript, komp)
        # Eigenschaft
        self.Anlage = komp.getProperty('Schnittstelle::Anlage').Value
        self.App = vcscript.getApplication()
        # Erstelle Datenbank/Tabelle falls notwendig
        self.konfig_db()
        # Importierte Funktionen
        self.delay = vcscript.delay
    
    def OnStart(self):
        """Ermittle alle Komponenten zu Simulationsbeginn, lege die Zeit zwischen den Datenbankzugriffen fest und den Pfad zur Datenbank.
        """
        # Eigenschaften  
        self.Alle_komp = {komp.Name : komp for komp in self.App.Components}
        if self.Anlage == 'real':
            self.Delay_zeit = 0.1
            self.Pfad = konst.PFAD_R_SIGNALE
            # Reset + Aktualisierung der DB
            self.reset_alle_db()
            self.update_komp_db()
        else:
            self.Delay_zeit = 0.05
            self.Pfad = konst.PFAD_V_SIGNALE
    
    def OnSignal(self, signal):
        pass

    def OnRun(self):
        """Lies die Informationen aus der jeweiligen Datenbank und signalisiere die jeweilige Komponente.
        """
        db = Datenbank(self.Pfad)
        # Gehe alle Datenbankzeilen durch und sende Signale an jeweilige Komponente
        while True:
            db_zeile = {}
            for zeile in db.get_all_data(konst.TABELLE_SIGNALE, sofort = False):
                db_zeile['Name'], db_zeile['Typ'], db_zeile['Funktion'], db_zeile['Info'] = zeile
                if db_zeile['Funktion']:
                    self.update_komp(db_zeile)
                    reset = (db_zeile['Name'], db_zeile['Typ'], '', '')
                    db.replace_query(konst.TABELLE_SIGNALE, reset)
            self.delay(self.Delay_zeit)
    
    def konfig_db(self):
        """Prüfe Datenbank und erstelle Tabelle falls notwendig.
        """
        # Erstelle und passe Datenbanken an
        for pfad, tabelle in self.PFADE_TABELLEN:
            if Datenbank(pfad) and os.stat(pfad).st_size != 0:
                continue
            felder = None
            if tabelle == 'Signale':
                felder = ('Name STRING PRIMARY KEY', 'Typ STRING NOT NULL', 'Funktion STRING', 'Info STRING')
            elif tabelle == 'Komponenten':
                felder = ('Name STRING PRIMARY KEY', 'Typ STRING NOT NULL')
            if felder:
                db = Datenbank(pfad)
                db.create_query(tabelle, felder)

    def konfig_komp(self, vcscript, komp):
        """Erstelle die Eigenschaft 'Schnittstelle::Anlage' die bestimmt, ob es sich um eine virtuelle oder reale Anlage handelt.

        Parameter
        - - - - -
        vcscript - module
            Modul vcScript
        komp - vcComponent
            diese Komponente
        """
        # Eigenschaft
        if not komp.getProperty('Schnittstelle::Anlage'):
            self.Anlage = komp.createProperty(vcscript.VC_STRING, 'Schnittstelle::Anlage', vcscript.VC_PROPERTY_STEP)
            self.Anlage.StepValues = ['real', 'virtuell']
            self.Anlage.Value = 'real'

    def reset_alle_db(self):
        """Lösche alle Einträge in allen Datenbanken (real, virtuell und die für Steuerung).
        """
        # Lösche alle Einträge in den Tabellen aller Datenbanken
        for pfad, tabelle in self.PFADE_TABELLEN:
            db = Datenbank(pfad)
            db.delete_query(tabelle)
    
    def update_komp(self, db_zeile):
        """Signalisiere die Komponente über dessen StringSignal 'UpdateSignal' über die erhaltenen Informationen aus der Datenbank.

        Parameter
        - - - - - 
        db_zeile - dict
            Wörterbuch mit den Informationen (Index): Name, Typ, Funktion und Info
        """
        # Update-Informationen werden an die jeweilige Komponente weitergereicht
        signal_wert = repr({key:db_zeile[key] for key in ('Funktion', 'Info')})
        # Kurzfristige Updates an Komponenten werden mit + markiert, um andere Updates in der DB nicht zu überschreiben
        name = db_zeile['Name'].replace('+','')
        komp = self.Alle_komp[name]
        komp.findBehaviour('UpdateSignal').signal(signal_wert)
    
    def update_komp_db(self):
        """Schreibe die Namen und Typen aller Komponenten in die Datenbank für die Steuerung.
        """
        # Aktualisiere die Komponenten-Datenbank mit den Namen und Typen der Komponenten
        db = Datenbank(konst.PFAD_KOMP)
        for name, komp in self.Alle_komp.items():
            typ = komp.getProperty('Schnittstelle::Typ')
            if typ and typ.Value:
                parameter = (name, typ.Value)
                db.replace_query(konst.TABELLE_KOMP, parameter)
        


    
    

    

    

    
    

    

    
    


    


    
