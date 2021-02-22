#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .datenbank import Datenbank
from ast import literal_eval
import konst

class Upvia(object):
    """Upvia = Update virtuelle Anlage. Enthält Methoden und Eigenschaften zum Erstellen und Entfernen von Komponenten auf dem Förderband
    durch Vergleich der Signale der realen und virtuellen Anlage. 

    Attribute
    - - - - - 
    Aktuelle_komp - vcComponent
        letzte vom Sensor erfasste Komponente
    Alle_creator - vcComponent
        Referenz zur Komponente 'Creator' zum Erstellen von Komponenten
    Real - bool
        True, wenn ComponentSignal aus realer Anlage positiv ist
    Virtuell - bool
        True, wenn ComponentSignal positiv ist
    
    Methoden
    - - - - -
    ermittle_nahe_komp(path, path_distanz) -> vcComponent
        sucht nach der nächsten Komponente auf dem Pfad vor dem Sensor und gibt diese zurück
    erstelle_komponente(prod_name, path, position) -> vcComponent
        erstellt Komponente am Sensor und gibt diese zurück
    reset_OnStart(app) -> None
        resettet Attribute; sollte im OnStart-Event aufgerufen werden
    update_db(name, typ, funktion, info) -> None
        aktualisiert die (virtuelle) Datenbank mit obigen Informationen
    vergleiche_real(komp_signal) -> None
        vergleicht reale und virtuelle Signale; aufgerufen, wenn in virtueller Anlage Komponente erkannt wird
    vergleiche_virtuell(prod_name, path, path_distanz, position) -> None
        vergleicht reale und virtuelle Signale; aufgerufen, wenn Signal aus realer Anlage kommt

    """
    def __init__(self):
        """Nix
        """
        # Eigenschaften
        self.Alle_creator = None

    def ermittle_nahe_komp(self, path, path_distanz):
        """ Sucht nach der nächsten Komponente auf dem Pfad vor dem Sensor und gibt diese zurück.

        Es wird die Distanz zwischen dem Sensor und den Komponenten auf dem Pfad ermittelt und die nächste Komponente zurückgegeben.

        Parameter
        - - - - - 
        path - vcMotionPath
            der Pfad auf dem sich die Komponente bewegt
        path_distanz - float
            abstand zwischen Sensor und Pfadanfang

        """
        # Entferne nächste Komponente vor Sensor, falls existiert
        komps = path.Components
        if not komps:
            return
        komps_distanz = [path_distanz - komp.getPathDistance() for komp in komps]
        pos_distanz = [dist for dist in komps_distanz if dist>0]
        if not pos_distanz:
            return
        index = komps_distanz.index(min(pos_distanz))
        komp = komps[index]
        return komp

    def erstelle_komponente(self, prod_name, path, position):
        """Erstelle Komponente und positioniere an gleiche Stelle wie Sensor.
        Die Komponenten werden über die ComponentCreator der Komponente 'Creator' erstellt.

        Parameter
        - - - - - 
        prod_name : str
            name der zu erstellenden Komponente
        path : vcMotionPath
            Pfad auf dem sich die Komponenten bewegen
        position : vcMatrix
            Position des Sensors bezüglich des Welt-Koordinatensystem
        """
        creator = self.Alle_creator.findBehaviour(prod_name + '__HIDE__')
        komp = creator.create()
        komp.PositionMatrix = position
        path.grab(komp)
        return komp

    def reset_OnStart(self, app):
        """Attribute werden resettet. Komponente 'Creator' wird gesucht und Referenz gespeichert.

        Funktion soll im OnStart-Event aufgerufen werden.

        Parameter
        - - - - -
        app - vcApplication
            Referenz zur Anwendung
        """
        # Eigenschaften
        self.Aktuelle_komp = None
        if not self.Alle_creator:
            self.Alle_creator = app.findComponent('Creator')
        if not self.Alle_creator:
            print('Komponente "Creator" nicht gefunden!')
        self.Erstellte_komponente = None
        self.Real = False
        self.Virtuell = False

    def update_db(self, name, typ, funktion, info):
        """Aktualisiert die Datenbank für die virtuelle Datenbank mit neuen Informationen.

        Parameter
        - - - - - 
        name - str
            Name der Komponente
        typ - str
            Typ der Komponente
        funktion - str
            auszuführende Funktion
        info - str
            zusätzliche Informationen notwendig zum Ausführen der Komponente
        """
        # Aktualisiere die Datenbank. Signale gelangen so zur virtuellen Anlage.
        db = Datenbank(konst.PFAD_V_SIGNALE)
        parameter = (name, typ, funktion, info)
        db.replace_query(konst.TABELLE_SIGNALE, parameter)  
    
    def vergleiche_real(self, komp_signal):
        """Vergleicht reale und virtuelle Signale miteinander und entfernt je nachdem erkannte Komponente.

        Aufgerufen, wenn in der virtuellen Anlage eine Komponente erkannt wird.

        Wird in der virtuellen Anlage eine Komponente erkannt so wird die Referenz zu dieser gespeichert. Nach dem Übergang der 
        Komponente über den Sensor wird überprüft ob ein Signal von der realen Anlage kam. Wenn nicht, dann wird die Komponente 
        entfernt, außer es handelt sich um eine erstelle Komponente.

        Parameter
        - - - - - 
        komp_signal - vcComponentSignal
            ComponentSignal zum Erkennen von Komponenten
        """
        # Warte bis Komponente über Sensor und speicher Referenz zur Komponente 
        if komp_signal.Value:
            self.Virtuell = True
            self.Aktuelle_komp = komp_signal.Value
        else:
            # Entferne Komponente, falls nicht selbst erstellt oder kein Signal von realer Anlage
            if self.Aktuelle_komp and not self.Real and self.Aktuelle_komp != self.Erstellte_komponente:
                try:
                    self.Aktuelle_komp.delete()
                    self.Aktuelle_komp = None
                except:
                    self.Aktuelle_komp = None
            self.Virtuell = False
            self.Real = False
            

    def vergleiche_virtuell(self, prod_name, path, path_distanz, position):
        """Vergleicht virtuelle und reale Signale miteinander und erstellt je nachdem eine Komponente.

        Wird aufgerufen, wenn ein Signal von der realen Anlage kommt.

        Ist in der virtuellen Anlage keine Komponente, so wird die nächste Komponente auf dem Pfad vor dem Sensor ermittelt, 
        eine Komponente in Sensorposition erstellt und die vorher ermittelte Komonente, falls vorhanden, wird entfernt.

        Parameter
        - - - - - 
        prod_name - str
            Name des zu erstellenden Produkts
        path - vcMotionPath
            Pfad mit der die Komponenten transportiert werden
        path_distanz - float
            Distanz zwischen Sensor und Pfadanfang
        position - vcMatrix
            Sensorposition im Welt-Koordinatensystem
        """
        # Erhalte Names des Produkts aus der realen Anlage, damit dieser in der virtuellen Anlage hergestellt werden kann
        if prod_name:
            self.Real = True
        else:
            self.Real = False
        # Erstelle Produkt, falls bei der virtuellen Anlage der Sensor nicht aktiviert wurde und entferne nächste Komp zum Sensor
        if self.Real and not self.Virtuell:
            komp = self.ermittle_nahe_komp(path, path_distanz)
            self.Erstellte_komponente = self.erstelle_komponente(prod_name, path, position)
            if komp:
                komp.delete()

        


        

    
            
        
        



        
        
