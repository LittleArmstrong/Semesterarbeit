#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .upvia import Upvia
from ast import literal_eval

class Transportstelle(Upvia):
    """ Markiert die Stelle, von der Komponenten gegriffen bzw. zu der sie platziert werden sollen. 
    Erbt Methoden und Eigenschaften der Klasse Upvia. 
    Pythonscript in Script umbenennen und in Komponente 'Bundler Point' in 'Conveyor Utilities' im eCatalog einfügen.
    Der vorhandene Script namens 'PythonScript' sollte entfernt oder überschrieben werden.
     
    Scriptinhalt:
    import vcScript
    from vccode import Transportstelle

    komptyp = Transportstelle(vcScript)

    def OnStart():
        komptyp.OnStart()
    
    def OnSignal(signal):
        komptyp.OnSignal(signal)
    
    def OnRun():
        komptyp.OnRun()
    
    Attribute
    - - - - - 
    TYP : str
        Konstante zum Kennzeichnen der Komponente für die Steuerung (GUI) und Datenbank
    Anlage : str
        ob real oder virtuell; bestimmt die Funktionen der Komponenten
    App : vcApplication
        Referenz zur Anwendung
    Bool_signal : vcBoolSignal
        Referenz zur BoolSignal-Verhaltensweise, welches mit dem Sensor verbunden ist
    Container : vcContainer
        Verhaltensweise 'ComponentContainer__HIDE__'
    Interface : vcSimInterface
        Verhaltensweise 'PathInterface'
    Komponente : vcComponent
        Referenz zur Komponente selbst
    Komp_signal : vcComponentSignal
        Referenz zur ComponentSignal-Verhaltensweise, welches mit dem Sensor verbunden ist
    Name : str
        Name der Komponente
    Path : vcMotionPath
        Referenz zum Pfad des Förderbands auf dem diese Komponente platziert ist
    Path_distanz : float
        Distanz zwischen dieser Komponente und dem Anfang des Pfads
    Stop : vcBoolean
        Eigenschaft 'Schnittstelle::Stop'
    Stopp_komp : vcComponent
        Referenz zur gestoppten Komponente
    Update_signal : vcStringSignal
        Verhaltensweise 'UpdateSignal'
    Vcscript : module
        Modul vcScript
    Weltposition : vcMatrix
        Position dieser Komponente im Welt-Koordinatensystem
    
    Methoden
    - - - - -
    OnStart() -> None
        Event - resettet bestimmte Attribute am Anfang der Simulation
    OnSignal(signal) -> None
        Event - führt Funktionen abh. vom Signal und Signalwert aus
    OnRun() -> None
        nix
    check_path() -> vcMotionPath
        ermittelt Pfad vom Förderband mit der diese Komponente verbunden ist
    konfig_komp(vcscript) -> None
        erstellt Verhaltensweisen/Eigenschaften falls notwendig und verbindet Signale mit diesem Script
    """
    
    def __init__(self, vcscript):
        """
        Parameter
        - - - - - 
        vcscript - module
            Modul vcScript
        """
        # Funktionen und Methoden der Oberklasse
        super(Transportstelle, self).__init__()
        # Konstanten
        self.TYP = 'Transportstelle'
        # Variablen
        app = vcscript.getApplication()
        komp = vcscript.getComponent()
        sensor = komp.findBehaviour('ComponentPathSensor')
        try:
            self.Anlage = app.findComponent('Schnittstelle').getProperty('Schnittstelle::Anlage').Value
        except:
            print('Komponente Schnittstelle bzw. dessen Eigenschaft Anlage fehlt!')
        # Eigenschaften
        self.App = app
        self.Bool_signal = sensor.BoolSignal
        self.Container = komp.findBehaviour('ComponentContainer__HIDE__')
        self.Interface = komp.findBehaviour('PathInterface')
        self.Komponente = komp 
        self.Komp_signal = sensor.ComponentSignal
        self.Name = komp.Name
        self.Stop = komp.getProperty('Schnittstelle::Stop')
        self.Update_signal = komp.findBehaviour('UpdateSignal')
        self.Vcscript = vcscript
        # Erstelle Verhaltensweisen und Eigenschaften falls notwendig
        self.konfig_komp(vcscript)
    
    def OnStart(self):
        """Resette Attribute beim Starten
        """
        # Eigenschaften der Klasse upvia initialisert/resettet
        self.reset_OnStart(self.App)
        # Objekt-Eigenschaften
        self.Path = self.check_path()
        if self.Anlage == 'virtuell':
            self.Path_distanz = self.Komponente.PositionMatrix.P.X
            self.Stopp_komp = None
            self.Weltposition = self.Komponente.WorldPositionMatrix
    
    def OnSignal(self, signal):
        """Aufgerufen wenn bei verbundenen Signalen der Wert sich verändert. 
        Bool- und ComponentSignal rufen dieses Event auf, nachdem eine Komponente erfasst wurde.
        StringSignal namens UpdateSignal überreicht Informationen zur Ausführung von Funktionen.

        real :
        Bool- und ComponentSignal aktualisieren die Datebank mit dem Komponentennamen als Info.
        ComponentSignal - Stoppe Komponente, falls Eigenschaft 'Stop' positiv.

        virtuell :
        ComponentSignal - entferne Komponente, wenn kein positives Signal aus Datenbank und stopp
            Komponente, wenn Eigenschaft 'Stop' positiv.
        UpdateSignal
        - Funktion :
            'signal' - Komponentenname
                erstelle Komponente, falls keine da

        Parameter
        - - - - - 
        signal - vcBoolSignal, vcComponentSignal, vcStringSignal
        """
        if self.Anlage == 'real':
            if signal == self.Komp_signal:
                if signal.Value:
                    self.update_db(self.Name, self.TYP, 'signal', signal.Value.Name)
                    if self.Stop.Value:
                        self.Stopp_komp = signal.Value
                        self.Stopp_komp.stopMovement()
                else:
                    self.update_db(self.Name, self.TYP, 'signal', '')
            elif signal == self.Bool_signal and signal.Value:
                if self.Container.Components:
                    part = self.Container.Components[0]
                    self.update_db(self.Name, self.TYP, 'signal', part.Name)
                    self.Path.grab(part)
        if self.Anlage == 'virtuell':
            if signal == self.Update_signal:
                update = literal_eval(signal.Value)
                if update['Funktion'] == 'signal':
                    if update['Info']:
                        self.vergleiche_virtuell(update['Info'], self.Path, self.Path_distanz, self.Weltposition)
                    elif self.Stopp_komp:
                        self.Stopp_komp.delete()
                        self.Stopp_komp = None
            elif signal == self.Komp_signal:
                self.vergleiche_real(signal)
                if signal.Value and self.Stop.Value:
                    self.Stopp_komp = signal.Value
                    self.Stopp_komp.stopMovement()
    
    def OnRun(self):
        pass
    
    def check_path(self):
        """Ermittle Pfad vom Förderband mit der diese Komponente verbunden ist.
        """
        komp = self.Interface.ConnectedComponent
        if not komp:
            return
        return komp.findBehavioursByType(self.Vcscript.VC_ONEWAYPATH)[0]
            
    def konfig_komp(self, vcscript):
        """ Erstelle Verhaltensweisen/Eigenschaften falls notwendig.
        Verhaltensweisen : 
        'UpdateSignal' - vcStringSignal
            zum weiterreichen der Informationen aus der Datenbank
        
        Eigenschaften :
        'Schnittstelle::Stop' - vcBoolean
            zum Stoppen der vom Sensor ermittelten Komponente
        'Schnittstelle::Typ' - vcString
            zum Kennzeichnen der Komponente für die Datenbank und Informationserfassung (UpdateSignal)

        Verbindungen mit diesem Script:
        'UpdateSignal'
        'ComponentSignal'
        'BoolSignal'

        Parameter
        - - - - - 
        vcscript - module
        """
        # Verhaltensweisen
        script = self.Komponente.findBehaviour('Script')
        if not self.Komponente.findBehaviour('UpdateSignal'):
            self.Update_signal = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
        # Eigenschaften
        if not self.Stop:
            self.Stop = self.Komponente.createProperty(vcscript.VC_BOOLEAN, 'Schnittstelle::Stop')
            self.Stop.Value = False
        typ = self.Komponente.getProperty('Schnittstelle::Typ')
        if not typ:
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP
        # Verbindungen
        self.Container.TransitionSignal = self.Bool_signal
        if not script:
            print(self.Name, 'Pythonscript in Script umbenennen und Layout neu laden.')
        else:
            signale = (self.Komp_signal, self.Bool_signal, self.Update_signal)
            for signal in signale:
                if script not in signal.Connections:
                    signal.Connections += [script]

    

        
    
          

 
    

    
    
