#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .datenbank import Datenbank
from ast import literal_eval
import konstanten

class Upvia(object):
    # __init__ und exklusive Funktionen
    def __init__(self):
        # Konstanten
        self.DB_PFAD = konstanten.PFAD_SIGNALE_VIRTUELL
        self.DB_TABELLE = konstanten.TABELLE_SIGNALE

        self.Alle_creator = None

    def ermittle_nahe_komp(self, path, path_distanz):
        # Entferne nächste Komponente vor Sensor, falls existiert
        komps = path.Components
        if not komps:
            return
        komps_distanz = [path_distanz- komp.getPathDistance() for komp in komps]
        pos_distanz = [dist for dist in komps_distanz if dist>0]
        if not pos_distanz:
            return
        index = komps_distanz.index(min(pos_distanz))
        komp = komps[index]
        return komp

    def erstelle_komponente(self, path, position):
        creator = self.Alle_creator.findBehaviour(self.Produktname+'__HIDE__')
        komp = creator.create()
        komp.PositionMatrix = position
        path.grab(komp)
        return komp

    # Reset + Initialisierung
    def reset_OnStart(self, app):
        # Referenz zur Creator-Komponente
        if not self.Alle_creator:
            self.Alle_creator = app.findComponent('Creator')
        # Objekt-Eigenschaften
        self.Aktuelle_komp = None
        self.Erstellte_komponente = None
        self.Produktname = None
        self.Real = False
        self.Virtuell = False

    def update_db(self, name, typ, funktion, wert):
        # Aktualisiere die Datenbank. Signale gelangen so zur virtuellen Anlage.
        db = Datenbank(self.DB_PFAD)
        parameter = (name, typ, funktion, wert)
        db.replace_query(self.DB_TABELLE, parameter)  
    
    def vergleiche_real(self, komp_signal):
        # Warte bis Komponente über Sensor und speicher Referenz zur Komponente 
        if komp_signal.Value:
            self.Virtuell = True
            self.Aktuelle_komp = komp_signal.Value
        else:
            # Entferne Komponente, falls nicht selbst erstellt oder kein Signal von realer Anlage
            if self.Aktuelle_komp and not self.Real and self.Aktuelle_komp != self.Erstellte_komponente:
                self.Aktuelle_komp.delete()
                self.Aktuelle_komp = None
            self.Virtuell = False
            self.Real = False

    def vergleiche_virtuell(self, produkt_name, path, path_distanz, position):
        # Erhalte Names des Produkts aus der realen Anlage, damit dieser in der virtuellen Anlage hergestellt werden kann
        self.Produktname = produkt_name
        self.Real = True
        # Erstelle Produkt, falls bei der virtuellen Anlage der Sensor nicht aktiviert wurde und entferne nächste Komp zum Sensor
        if not self.Virtuell:
            komp = self.ermittle_nahe_komp(path, path_distanz)
            self.Erstellte_komponente = self.erstelle_komponente(path, position)
            if komp:
                komp.delete()
            self.Real = False

        


        

    
            
        
        



        
        
