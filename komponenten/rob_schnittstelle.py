#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .datenbank import Datenbank
from ast import literal_eval
import konst
import os

class RobSchnittstelle():
    """Klasse zum Lesen udn Speichern der Gelenkwerte eines Roboters in der realen Anlage in einer Datenbank oder zum Bewegen der Roboter-
    gelenke anhand der von der Datenbank gelesenen Werte.

    Für jeden Roboter wird eine eigene Datenbank erstellt, um Datenbanksperrungen zu vermeiden und weil es schneller ist.

    Scriptinhalt:
    import vcScript
    import vcHelpers.Robot2 as vcRobot
    from vccode import RobSchnittstelle

    komptyp = RobSchnittstelle(vcScript, vcRobot)

    def OnStart():
        komptyp.OnStart()
    
    def OnRun():
        komptyp.OnRun()

    Attribute
    - - - - - 
    App - vcApplication
        Referenz zur Anwendung
    Delay_schreibe - float
        Zeit zwischen dem Speichern von Datenbankeinträgen
    Delay_lese - float
        Zeit zwischen dem Lesen von Datenbankeinträgen
    Name - str
        Name dieser Komponente für Fehlermeldungen
    Robotername - vcProperty
        Name des Roboters das überwacht werden soll
    Vcrobot - module
        vcHelpers.Robot2 Modul

    Importierte Funktionen
    - - - - - - - - - - - -
    delay(zeit) -> None
        stoppt die Ausführung des Scripts für bestimmte Zeit
    suspend() -> None
        stoppt die Ausführung des OnRun-Events

    Methoden
    - - - - -
    OnStart() -> None
        Event - ermittle Pfad, Referenz zum Roboter und erstelle und resette Datenbank zu SImulationsbeginn
    OnRun() -> None
        abh. von der Anlage: real -  lies Gelenkwerte aus Datenbank; virtuell - speicher Gelenkwerte in Datenbank
    konfig_db -> None
        erstelle Datenbank mit bestimmter Tabelle wenn nicht vorhanden
    konfig_komp() -> None
        erstelle Eigenschaft Robotername
    reset_db() -> None
        Lösch alle Einträge in der Datenbank
    """
    def __init__(self, vcscript, vcrobot):
        """
        Parameter
        - - - - -
        vcscript - vcScript
            Modul vcScript
        vcrobot - vcRobot
            Modul vcHelpers.Robot2
        """
        app = vcscript.getApplication()
        komp = vcscript.getComponent()
        self.App = app
        self.Delay_schreibe = 0.05
        self.Delay_lese = 0.06
        self.Name = komp.Name
        self.Robotername = komp.getProperty('Schnittstelle::Robotername')
        self.Vcrobot = vcrobot
        # Erstelle Eigenschaften, Verhaltensweisen
        self.konfig_komp(vcscript, komp)
        # Importierte Funktionen
        self.delay = vcscript.delay
        self.suspend = vcscript.suspendRun

    def OnStart(self):
        """Datenbankname ist gleich dem leicht modifizierten Roboternamen, um den Pfad eindeutig indentifizieren zu können.
        Dann wird eine Datenbank erstellt, falls nicht vorhanden und alle Einträge zu Simulationsbeginn gelöscht.
        """
        try:
            self.Anlage = self.App.findComponent('Schnittstelle').getProperty('Schnittstelle::Anlage').Value
        except:
            print('Komponente Schnittstelle bzw. dessen Eigenschaft Anlage fehlt!')
        if self.Robotername.Value:
            self.Pfad = konst.PFAD + self.Robotername.Value.replace('#','').replace(' ','_') + '.db'
        else:
            print(self.Name, 'Bitte Roboternamen eingeben und neu starten.')
        self.Roboter = self.App.findComponent(self.Robotername.Value)
        if self.Anlage == 'real' and self.Pfad:
            self.konfig_db(self.Pfad, konst.TABELLE_SIGNALE, konst.FELDER_ROBOTER)
            self.reset_db(self.Pfad, konst.TABELLE_SIGNALE)
        
    def OnRun(self):
        """Referenz zur Robotersteuerung und dem vcRobot-Objekt des Roboters, um die Gelenkwerte abh. von der Anlage zu ermitteln (real) 
        und zu bewegen (virtuell). Die Gelenkwerte werden in der erstellten Datenbank periodisch gespeichert und gelesen.

        Durch die Attribute Delay_schreiben und Delay_lesen sowie dem Limit im SQL-Query kann die Roboterbewegung in der virtuellen Anlage
        beeinflusst werden. Z.B. Je kleiner der Limit desto schneller aber auch ruckartiger die Bewegungen des Roboters und umgekehrt.
        """
        if not self.Roboter:
            print(self.Name, 'Roboter {} nicht gefunden! Bitte Roboternamen eingeben und neu starten.'.format(self.Robotername.Value))
            self.suspend()
        self.Vcrob = self.Vcrobot.getRobot(self.Roboter)
        db = Datenbank(self.Pfad)
        con = self.Roboter.findBehaviour('Controller')
        gelenke = con.Joints
        if self.Anlage == 'real':
            while True:
                gelenk_werte = [g.CurrentValue for g in gelenke]
                db.insert_query(konst.TABELLE_SIGNALE, (repr(gelenk_werte),))
                self.delay(self.Delay_schreibe)
        elif self.Anlage == 'virtuell':
            query='SELECT rowid, Gelenkwerte FROM {} WHERE rowid > ? ORDER BY rowid DESC Limit 1'.format(konst.TABELLE_SIGNALE)
            id=0
            while True:
                self.delay(self.Delay_lese)
                zeilen = db.query(query, (id,), sofort=True)
                zeilen.reverse()
                for zeile in zeilen:
                    id = zeile[0]
                    werte = literal_eval(zeile[1])
                    self.Vcrob.driveJoints(*werte)
                

    def konfig_db(self, pfad, tabelle, felder):
        """Prüfe Datenbank und erstelle Tabelle falls notwendig.

        Parameter
        - - - - -
        pfad - str
            Pfad zur Datenbank
        tabelle - str
            Name der Tabelle
        felder - list
            die Spalten der Tabelle; Beispiel: ('Name STRING PRIMARY KEY', 'ID INTEGER')
        """
        if Datenbank(pfad) and os.stat(pfad).st_size == 0:
            db = Datenbank(pfad)
            db.create_query(tabelle, felder)
        
    def konfig_komp(self, vcscript, komp):
        """Erstelle die Eigenschaft Robotername durch die der zu überwachende Roboter bestimmt wird.
        
        Parameter
        - - - - -
        vscript - vcScript
            Modul vcScript
        komp - vcComponent
            diese Komponente
        """
        if not self.Robotername:
            self.Robotername = komp.createProperty(vcscript.VC_STRING, 'Schnittstelle::Robotername')
    
    def reset_db(self, pfad, tabelle):
        """Lösche alle Einträge in der gewählten Tabelle.

        Parameter
        - - - - - 
        pfad - str
            Pfad zur Datenbank
        tabelle - str
            Name der Tabelle
        """
        db = Datenbank(pfad)
        db.delete_query(tabelle)