#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ast import literal_eval
from upvia import Upvia

class Maschine():
    """Klasse zum Steuern der Maschinen. 
    Frame 'ProcessLocation' sollte an Frame 'ProductLocation' im Root-Feature der Root-Node angedockt werden.
    werden.

    Pythonscript namens 'Script':
    import vcScript
    from vccode import Maschine

    komptyp = Maschine(vcScript)

    def OnStart():
        komptyp.OnStart()
    
    def OnSignal(signal):
        komptyp.OnSignal(signal)
    
    def OnRun():
        komptyp.OnRun()
    
    Attribute
    - - - - -
    TYP - str
        Konstante zum Kennzeichnen der Komponente für die Steuerung (GUI) und Datenbank
    Anfangsprodukt - vcString
        unbearbeitetes Produkt
    Anlage - str
        ob virtuelle oder reale Anlage
    App - vcApplication
        Referenz zur Anwendung
    Auf - vcBoolSignal
        zum Öffnen der Türe
    Belegt - vcBoolSignal
        ob Maschine belegt oder nicht
    Container - vcComponentContainer
        zum Aufbewahren der Komponente
    Container_in - vcConnector
        Input des Containers
    Creators - list of vcComponentCreator
        Liste aller ComponentCreator in der Maschine
    Endprodukt - vcString
        bearbeitetes Produkt
    istArbeiten - vcBoolSignal
        signalisiert, ob Prozess aktiv oder nicht
    istAuf - vcBoolSignal
        ob Türe offen
    istZu - vcBoolSignal
        ob Türe zu
    Komp - vcComponent
        Referenz zur Maschine
    Name - str
        Name der Maschine
    Prozesszeit - vcReal
        Zeit bis Prozess fertig
    Start - vcBoolSignal
        zum Starten des Prozesses
    Zu - vcBoolSignal
        zum schließen der Türe

    Importierte Funktionen
    - - - - - - - - - - - -
    resume() -> None
        führt das OnRun-Event fort
    suspend() -> None
        stopp das OnRun-Event
    update_db(name, typ, funktion, info) -> None
        aktualisiert die Datenbank für die virtuelle Anlage mit neuen Informationen
    
    Methoden
    - - - - -
    OnStart() -> None
        Event - Resettet Attribute und stellt die ComponentCreator ein
    OnSignal(signal) -> None
        Event - führt verschiedene Funktionen abh. vom Signal aus
    OnRun() -> None
        Event - geht automatisch alle Prozessschritte durch, wenn auf automatisch gestellt wurde
    erstelle_komp(komp_name) -> None
        erstellt Komponente in Maschine
    end_prozess() -> None
        beendet den Maschinenprozess
    konfig_komp(vcscript, komp) -> None
        erstellt notwendige Verhaltensweisen/Eigenschaften und verbindet die benötigten Signale mit diesem Script
    start_prozess() -> None
        startet den Maschinenprozess
    switch_prozess() -> None
        wechselt zwischen manueller und automatischer Steuerung
    update_prozesszeit(zeit_str) -> None
        legt die Prozesszeit fest
    
    """
    def __init__(self, vcscript):
        """
        Parameter
        - - - - -
        vcscript - module
            Modul vcScript
        """
        # Konstanten
        self.TYP = 'Maschine'
        # Referenz zur Komponente
        app = vcscript.getApplication()
        komp = vcscript.getComponent()
        # Verhaltensweisen der Komponente
        self.Anfangsprodukt = komp.getProperty('Schnittstelle::Anfangsprodukt')
        try:
            self.Anlage = app.findComponent('Schnittstelle').getProperty('Schnittstelle::Anlage').Value
        except:
            print('Komponente Schnittstelle bzw. dessen Eigenschaft Anlage fehlt! Bitte erstellen und neu starten.')
        self.App = app
        self.Auf = komp.findBehaviour('FROM_PLC_OpenDoor')
        self.Belegt = komp.findBehaviour('TransSignal')
        self.Container = komp.findBehaviour('ProcessContainer__HIDE__')
        self.Container_in = self.Container.getConnector('Input')
        self.Creators = komp.findBehavioursByType(vcscript.VC_COMPONENTCREATOR)
        self.Endprodukt = komp.getProperty('Schnittstelle::Endprodukt')
        self.istArbeiten = komp.findBehaviour('TO_PLC_ProcessIsRunning')
        self.istAuf = komp.findBehaviour('TO_PLC_DoorIsOpen')
        self.istZu = komp.findBehaviour('TO_PLC_DoorIsClosed')
        self.Komp = komp
        self.Name = komp.Name
        self.Prozesszeit = komp.getProperty('ProcessTime')
        self.Start = komp.findBehaviour('FROM_PLC_StartProcess')
        self.Zu = komp.findBehaviour('FROM_PLC_CloseDoor')
        # Importierte Funktionen
        self.resume = vcscript.resumeRun    
        self.suspend = vcscript.suspendRun
        self.update_db = Upvia().update_db
        # Erstelle notwendige Verhaltensweisen oder Eigenschaften  
        self.konfig_komp(vcscript, komp)
    
    def OnStart(self):
        """Resettet Attribute und stellt Name und zu erstellende Produkte der ComponentCreator ein.

        Name wird nach dem zu erstellenden Produkt benannt, um diesen einfacher auszuwählen.
        """
        try:
            produkte = [self.Anfangsprodukt.Value, self.Endprodukt.Value]
            for i in range(len(produkte)):
                self.Creators[i].Name = produkte[i] + '__HIDE__'
                self.Creators[i].Part = self.App.findComponent(produkte[i]).Uri
        except:
            print(self.Name, 'Anfangs- und Endprodukte im Layout nicht gefunden!')
        if self.Anlage == 'real':
            self.Fertig = False
            self.Steuerung = 'automatisch'
            self.istAuf.signal(True)
        
    def OnSignal(self, signal):
        """Steuert die Maschine abh. von den Signalen.
        'UpdateSignal'
        - Funktionen:
        real :
        'auto' - /
            wechselt zwischen Automatik und Manuell
        'zeit' - str
            legt die Prozesszeit fest
        'auf' - /
            öffnet die Türen
        'zu' - /
            schließt die Türen
        'start' - /
            startet den Prozess
        
        virtuell :
        'start' - str
            legt die Prozesszeit fest und startet dann den Prozess
        'fertig' - /
            signalisiert das Ende des Prozesses
        'auf' - str
            öffnet Türe und erstellt Produkt falls fertig
        'zu' - str
            schließt Türe und erstellt Produkt falls notwendig
        'frei' - /
            entfernt Komponente in Maschine
        
        real :
        Belegt - 'TransSignal'
        Sende Informationen an Datenbank

        istArbeite - 'TO_PLC_ProcessIsRunning'
        Sende Informationen an Datenbank falls wahr, ansonsten erstelle Endprodukt

        Auf - 'FROM_PLC_OpenDoor'
        Sende Informationen an Datenbank zusammen mit dem Namen der Komponente in der Maschine

        Zu - 'FROM_PLC_CloseDoor'
        Sende Informationen an Datenbank zusammen mit dem Namen der Komponente in der Maschine

        Parameter
        - - - - -
        signal - vcStringSignal, vcBoolSignal
        """
        if self.Anlage == 'real':
            if signal.Name == 'UpdateSignal':
                update = literal_eval(signal.Value) 
                if update['Funktion'] == 'auto':
                    self.switch_auto()
                else:
                    self.Steuerung = 'manuell'
                if update['Funktion'] == 'zeit':
                    self.update_prozesszeit(update['Info'])
                elif update['Funktion'] == 'auf':
                    self.Zu.signal(False)
                    self.Auf.signal(True)
                elif update['Funktion'] == 'zu':
                    self.Auf.signal(False)
                    self.Zu.signal(True)
                elif update['Funktion'] == 'start':
                    self.Start.signal(True)
            elif signal == self.Belegt:
                if signal.Value and self.Container.Components[0].Name == self.Anfangsprodukt.Value:
                    self.update_db(self.Name, self.TYP, 'belegt', self.Anfangsprodukt.Value)
                    self.Fertig = False
                    self.resume()
                elif signal.Value and self.Container.Components[0].Name == self.Endprodukt.Value:
                    self.update_db(self.Name, self.TYP, 'belegt', self.Endprodukt.Value)
                    self.Fertig = True
                elif signal.Value:
                    self.Fertig = False
                    self.resume()
                elif not signal.Value and not self.Container.Components:
                    self.update_db(self.Name, self.TYP, 'frei', '')
            elif signal == self.istArbeiten:
                if signal.Value:
                    self.update_db(self.Name, self.TYP, 'start', self.Prozesszeit.Value)
                else:
                    if self.Container.Components and self.Container.Components[0].Name == self.Anfangsprodukt.Value:
                        for komp in self.Container.Components:
                            komp.delete()
                        self.erstelle_komp(self.Endprodukt.Value)
                    self.Fertig = True
                    self.resume()
            elif signal == self.Auf:
                komp_name=''
                if self.Container.Components:
                    komp_name = self.Container.Components[0].Name
                self.update_db(self.Name, self.TYP, 'auf', komp_name)
            elif signal == self.Zu:
                komp_name=''
                if self.Container.Components:
                    komp_name = self.Container.Components[0].Name
                self.update_db(self.Name, self.TYP, 'zu', komp_name)
        elif self.Anlage == 'virtuell':
            if signal.Name == 'UpdateSignal':
                update = literal_eval(signal.Value)
                if update['Funktion'] == 'start':
                    self.Prozesszeit.Value = int(update['Info'])
                    self.Start.signal(True)
                    self.Fertig = False ##
                elif update['Funktion'] == 'fertig':
                    self.Fertig = True ##
                    self.Start.signal(False)
                elif update['Funktion'] == 'auf':
                    if update['Info']:
                        if self.Container.Components and self.Fertig: ###
                            for komp in self.Container.Components:
                                komp.delete()
                        self.erstelle_komp(update['Info'])
                    self.Zu.signal(False)
                    self.Auf.signal(True)
                elif update['Funktion'] == 'zu':
                    if update['Info']:
                        for komp in self.Container.Components:
                            komp.delete()
                        self.erstelle_komp(update['Info'])
                    self.Auf.signal(False)
                    self.Zu.signal(True)
                elif update['Funktion'] == 'frei':
                    for komp in self.Container.Components:
                        komp.delete()

    def OnRun(self):
        """Schließ Türe und starte Prozess oder beende Prozess und öffne Türe, wenn Maschine auf automatisch gestellt wurde.
        """
        while True:
            self.suspend()
            if self.Anlage == 'real' and self.Steuerung == 'automatisch':
                if self.istAuf and not self.Fertig: 
                    self.start_prozess()
                elif self.istZu and self.Fertig:
                    self.end_prozess()     
    
    def erstelle_komp(self, komp_name):
        """Erstelle bestimmte Komponente und füge diese der Maschine zu.

        Um das Endprodukt am Ende des Prozesses dahinzustellen oder um sicherzustellen, dass die richtigen Produkte, abh. von 
        den gegebenen Informationen aus der Datenbank in der Maschine sind.
        """
        creator = self.Komp.findBehaviour(komp_name + '__HIDE__')
        if not creator:
            creator = self.Komp.findBehaviour(self.Anfangsprodukt.Value + '__HIDE__')
        creator.getConnector('Output').connect(self.Container_in)
        creator.create()

    def end_prozess(self):
        """Stelle die Signale so ein, dass das Prozess beendet wurde und die Türen geöffnet werden.
        """
        self.Zu.signal(False)
        self.Start.signal(False)
        self.Auf.signal(True)

    def konfig_komp(self, vcscript, komp):
        """Erstelle Verhaltensweisen und Eigenschaften und Verbinde die Signale mit diesem Script.

        Verhaltensweisen :
        'UpdateSignal' - vcStringSignal
            Signal zum Weiterreichen der Informationen aus der Datenbank
        'Creatori__HIDE__' - vcComponentCreator
            erstelle zwei Creator für das Anfangs- und Endprodukt
        
        Eigenschaften :
        'Schnittstelle::Typ' - vcString
            zum Kennzeichnen der Komponente für die Datenbank und Informationserfassung (UpdateSignal)
        'Schnittstelle::Anfangsprodukt' - vcString
            Name des unfertigen Produktes
        'Schnittstelle::Endprodukt' - vcString
            Name des fertigen Produktes
        
        Verbindungen mit Script:
        'UpdateSignal'
        Belegt - 'TransSignal'
        istAuf - 'TO_PLC_DoorIsOpen'
        istZu - 'TO_PLC_DoorIsClosed'
        istArbeiten - 'TO_PLC_ProcessIsRunning'
        Auf - 'FROM_PLC_OpenDoor'
        Zu - 'FROM_PLC_CloseDoor'
        Start - 'FROM_PLC_StartProcess'

        Parameter
        - - - - - 
        vcscript - module
            Modul vcScript
        komp - vcComponent
            die Maschine
        """
        # Referenz zu Script
        script = komp.findBehaviour('Script')
        # Verhaltensweisen
        update_signal = komp.findBehaviour('UpdateSignal')
        if not update_signal:
            update_signal = komp.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
        if len(self.Creators) < 2:
            for i in range(2-len(self.Creators)):
                creator = komp.createBehaviour(vcscript.VC_COMPONENTCREATOR, 'Creator{}__HIDE__'.format(i))
                creator.Limit = 0
                creator.Interval = 0
            self.Creators = komp.findBehavioursByType(vcscript.VC_COMPONENTCREATOR)
        # Eigenschaften
        if not self.Anfangsprodukt:
            self.Anfangsprodukt = komp.createProperty(vcscript.VC_STRING, 'Schnittstelle::Anfangsprodukt')
        if not self.Endprodukt:
            self.Endprodukt = komp.createProperty(vcscript.VC_STRING, 'Schnittstelle::Endprodukt')
        if not komp.getProperty('Schnittstelle::Typ'):
            typ = komp.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP
        # Verbindungen zum Script
        if not script:
            print(self.Name, 'Pythonscript in Script umbenennen und Layout neu laden.')
        else:
            signale = [update_signal, self.Belegt, self.istAuf, self.istZu, self.istArbeiten, self.Auf, self.Zu, self.Start]
            for signal in signale:
                if script not in signal.Connections:
                    signal.Connections += [script]
        if not komp.findFeature('ProcessLocation'):
            print('Bitte Frame "ProcessLocation" an Frame "ProductLocation" im Root-Feature der Root-Node andocken')

    def start_prozess(self):
        """Starte den Prozess. Türe zu, Prozess start.
        """
        self.Auf.signal(False)
        self.Zu.signal(True)
        self.Start.signal(True)

    def switch_auto(self):
        """Wenn automatisch dann manuell und umgekehrt.
        """
        # Wechsel zwischen Manuell und Automatik
        if self.Steuerung == 'automatisch':
            self.Steuerung = 'manuell'
        else:
            self.Steuerung = 'automatisch'
            self.resume()
    
    def update_prozesszeit(self, zeit_str):
        """Lege die Prozesszeit fest, solange diese nicht null ist.
        """
        # Änder die Prozesszeit, falls nicht null
        zeit = int(zeit_str)
        if zeit:
            self.Prozesszeit.Value = zeit



        
    