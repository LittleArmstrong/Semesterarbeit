from .datenbank import Datenbank
from ast import literal_eval
import os
import konstanten

class Schnittstelle():
    def __init__(self, vcscript):
        # Datenbank-Konstanten
        self.PFAD_DATENBANK_REAL = konstanten.PFAD_SIGNALE_REAL
        self.PFAD_DATENBANK_VIRTUELL = konstanten.PFAD_SIGNALE_VIRTUELL
        self.PFAD_DATENBANK_KOMPONENTEN = konstanten.PFAD_KOMPONENTEN
        self.TABELLE_DATENBANK_SIGNALE = konstanten.TABELLE_SIGNALE
        self.TABELLE_DATENBANK_KOMPONENTEN = konstanten.TABELLE_KOMPONENTEN
        self.DATENBANK_PFADE_MIT_TABELLEN = [(self.PFAD_DATENBANK_REAL, self.TABELLE_DATENBANK_SIGNALE), \
            (self.PFAD_DATENBANK_VIRTUELL, self.TABELLE_DATENBANK_SIGNALE),\
            (self.PFAD_DATENBANK_KOMPONENTEN, self.TABELLE_DATENBANK_KOMPONENTEN)]

        # Referenz zur Komponente
        self.Komponente = vcscript.getComponent()
        
        # Referenz zu allen Komponenten
        alle_komponenten = vcscript.getApplication().Components
        self.Alle_komponenten = {komponente.Name : komponente for komponente in alle_komponenten}

        # Erstelle notwendige Eigenschaften und Behaviours
        self.konfiguriere_komponente(vcscript)

        # Eigenschaften des Objekts  
        self.Anlage = self.Komponente.getProperty('Schnittstelle::Anlage').Value

        # Importierte Funktionen
        self.delay = vcscript.delay

        # Erstelle Tabelle, falls Datenbank neu erstellt wurde
        self.konfiguriere_datenbanken()
        
    def OnRun(self):
        if self.Anlage == 'real':
            db = Datenbank(self.PFAD_DATENBANK_REAL)
            delay_zeit = 0.4
        elif self.Anlage == 'virtuell':
            db = Datenbank(self.PFAD_DATENBANK_VIRTUELL)
            delay_zeit = 0.2
        tabelle = self.TABELLE_DATENBANK_SIGNALE

        while True:
            alle_datenbank_zeilen = db.get_all_data(tabelle, sofort = False)
            datenbank_zeile = {}
            update_datenbank = []

            for zeile in alle_datenbank_zeilen:
                datenbank_zeile['Name'], datenbank_zeile['Typ'], datenbank_zeile['Funktion'], datenbank_zeile['Info'] = zeile
                if datenbank_zeile['Funktion']:
                    self.update_komponente(datenbank_zeile)
                    self.reset_zeile(update_datenbank, datenbank_zeile)

            for zeile in update_datenbank:
                db.replace_query(tabelle, zeile)
            self.delay(delay_zeit)

    def OnStart(self):        
        if self.Anlage == 'real':
            self.reset_alle_datenbanken()
            self.update_komponenten_datenbank()

    def OnSignal(self, signal):
        pass

    def konfiguriere_komponente(self, vcscript):
        if not self.Komponente.getProperty('Schnittstelle::Anlage'):
            self.Anlage = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Anlage')

    def konfiguriere_datenbanken(self):
        for pfad, tabelle in self.DATENBANK_PFADE_MIT_TABELLEN:
            if Datenbank(pfad) and os.stat(pfad).st_size == 0:
                felder_mit_typen = ''
                if tabelle == 'Signale':
                    felder_mit_typen = ('Name STRING PRIMARY KEY', 'Typ STRING NOT NULL', 'Funktion STRING', 'Info STRING')
                elif tabelle == 'Komponenten':
                    felder_mit_typen = ('Name STRING PRIMARY KEY', 'Typ STRING NOT NULL')

                if felder_mit_typen:
                    db = Datenbank(pfad)
                    db.create_query(tabelle, felder_mit_typen)

    def reset_alle_datenbanken(self):
        for pfad, tabelle in self.DATENBANK_PFADE_MIT_TABELLEN:
            db = Datenbank(pfad)
            db.delete_query(tabelle)

    def reset_zeile(self, liste, zeile):
        db_zeile = [zeile['Name'], zeile['Typ'], '', '']
        liste.append(db_zeile)

    def update_komponenten_datenbank(self):
        for name, komponente in self.Alle_komponenten.items():
            db = Datenbank(self.PFAD_DATENBANK_KOMPONENTEN)
            typ = komponente.getProperty('Schnittstelle::Typ')
            if typ and typ.Value:
                parameter = (name, typ.Value)
                db.replace_query(self.TABELLE_DATENBANK_KOMPONENTEN, parameter)

    def update_komponente(self, datenbank_zeile):
        signal_wert = repr({key:datenbank_zeile[key] for key in ('Funktion', 'Info')})
        komponente = self.Alle_komponenten[datenbank_zeile['Name']]
        signal = komponente.getBehaviour('UpdateSignal')
        signal.signal(signal_wert)
    


    


    
