#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .datenbank import Datenbank
from ast import literal_eval
import konstanten

class Upvia(object):
    # __init__ und exklusive Funktionen
    def __init__(self, komptyp):
        # Konstanten
        self.DB_PFAD = konstanten.PFAD_SIGNALE_VIRTUELL
        self.DB_TABELLE = konstanten.TABELLE_SIGNALE
        # Eigenschaften
        # Komptyp sollte folgende Eigenschaften besitzen
        # TYP - Funktion: update_db
        # App - Funktion: ermittle_creators
        # Container - Funktion: erstelle_komponente
        # Komp_signal - Funktion: vergleiche_real
        # Komponente - Funktion: ermittle_creators, update_db
        # Path - Funktion: erstelle_komponente, entferne_komponente
        # Path_distanz - Funktion: entferne_komponente
        # Produkte - Funktion: ermittle_creators
        # Vcscript - Funktion: ermittle_creators
        # Weltposition - Funktion: erstelle_komponente
        self.Komptyp = komptyp

    
    def ermittle_creators(self):
        produkte = self.Komptyp.Produkte.Value
        alle_creator = None
        creators = {}
        # Erstelle abh. von Produktanzahl ComponentCreator
        if produkte:
            produkte = [prod.strip() for prod in produkte.split(',')]
            alle_creator = self.Komptyp.Komponente.findBehavioursByType(self.Komptyp.Vcscript.VC_COMPONENTCREATOR)
            diff = len(alle_creator) - len(produkte)
            if diff < 0:
                for i in range(diff*-1):
                    creator = self.Komptyp.Komponente.createBehaviour(self.Komptyp.Vcscript.VC_COMPONENTCREATOR, str(i))
                    creator.Limit = 0
                    creator.Interval = 0
                alle_creator = self.Komptyp.Komponente.findBehavioursByType(self.Komptyp.Vcscript.VC_COMPONENTCREATOR)
        # Speichere die ComponentCreator in einem Wörterbuch mit dem Produktnamen, das hergestellt wird, als Index
        for i, produkt in enumerate(produkte):
            creator = alle_creator[i]
            if creator.Name != produkt + '__HIDE__':
                creator.Name = produkt + '__HIDE__'
                uri = self.Komptyp.App.findComponent(produkt).Uri
                creator.Part = uri
            creators[produkt] = creator
        return creators
    
    def ermittle_nahe_komp(self):
        # Entferne nächste Komponente vor Sensor, falls existiert
        komps = self.Komptyp.Path.Components
        if not komps:
            return
        komps_distanz = [self.Komptyp.Path_distanz - komp.getPathDistance() for komp in komps]
        pos_distanz = [dist for dist in komps_distanz if dist>0]
        if not pos_distanz:
            return
        index = komps_distanz.index(min(pos_distanz))
        komp = komps[index]
        return komp

    def erstelle_komponente(self):
        # Erstelle Komponente am Sensor
        creator = self.Creators[self.Produktname]
        self.Komptyp.Container.getConnector('Input').connect(creator.getConnector('Output'))
        komp = creator.create()
        komp.PositionMatrix = self.Komptyp.Weltposition
        self.Komptyp.Path.grab(komp)
        return komp

    # Reset + Initialisierung
    def reset_OnStart(self):
        # Objekt-Eigenschaften
        self.Aktuelle_komp = None
        self.Creators = self.ermittle_creators()
        self.Erstellte_komponente = None
        self.Produktname = None
        self.Real = False
        self.Virtuell = False

    def update_db(self, funktion, wert):
        # Aktualisiere die Datenbank. Signale gelangen so zur virtuellen Anlage.
        db = Datenbank(self.DB_PFAD)
        parameter = (self.Komptyp.Komponente.Name, self.Komptyp.TYP, funktion, wert)
        db.replace_query(self.DB_TABELLE, parameter)  
    
    def vergleiche_real(self):
        # Warte bis Komponente über Signal. Speicher Komponente solange
        if self.Komptyp.Komp_signal.Value:
            self.Virtuell = True
            self.Aktuelle_komp = self.Komptyp.Komp_signal.Value
        else:
            # Entferne Komponente, falls nicht selbst erstellt oder kein Signal von realer Anlage
            if self.Aktuelle_komp and not self.Real and self.Aktuelle_komp != self.Erstellte_komponente:
                self.Aktuelle_komp.delete()
                self.Aktuelle_komp = None
            self.Virtuell = False
            self.Real = False

    def vergleiche_virtuell(self, produkt):
        # Erhalte Names des Produkts aus der realen Anlage, damit dieser in der virtuellen Anlage hergestellt werden kann
        self.Produktname = produkt
        self.Real = True
        # Erstelle Produkt, falls bei der virtuellen Anlage der Sensor nicht aktiviert wurde und entferne nächste Komp zum Sensor
        if not self.Virtuell:
            komp = self.ermittle_nahe_komp()
            self.Erstellte_komponente = self.erstelle_komponente()
            if komp:
                komp.delete()
            self.Real = False

        


        

    
            
        
        



        
        
