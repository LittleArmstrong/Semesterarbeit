#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .datenbank import Datenbank
from .upvia import Upvia
from ast import literal_eval

class Transport(Upvia):
    """ Für die Komponenten 'Sensor Conveyor', 'Conveyor' und 'Curve Conveyor'. Zum Vergleichen der virtuellen und realen
    Signalen und so Komponenten zu entfernen bzw. zu erstellen. Pythonscript namens 'Script' erstellen.

    Scriptinhalt :
    import vcScript
    from vccode import Transport

    komptyp = Transport(vcScript)

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
    App - vcApplication
        Referenz zur Anwendung
    Komp_signal - vcComponentSignal
        mit dem Sensor verbundener ComponentSignal zum signalisieren der erfassten Komponente
    Komponente - vcComponent
        diese Komponente
    Path - vcMotionPath
        erster gefundene OneWayPath
    Sensor - vcBehaviour
        mit dem Path verbundener ComponentPathSensor zum Erfassen von Komponenten auf dem Pfad

    Importierte Funktionen
    - - - - - - - - - - - -
    resume() -> None
        führe das OnRun-Event fort
    suspend() -> None
        stoppe das OnRun-Event

    Methoden
    - - - - -
    OnStart() -> None
        Event - legt Sensor-Frame fest (Curve Conveyor) und resettet Attribute
    OnSignal(signal) -> None
        Event - führt Funktionen abh. vom Signal und dessen Wert aus
    OnRun() -> None
        nix
    konfig_komp(vcscript, komp) -> None
        erstellt notwendige Verhaltensweisen und Eigenschaften und verbindet Signale mit diesem Script
    set_sensor_frame() -> None
        legt die Position des Sensors auf dem Pfad fest, falls dies nicht getan wurde; standard ist die Mitte
    umleite_komp(komp) -> None
        entfernt Komponente und erstellt eine Neue am gewählten Förderband 
    update_umleite(zu_komp) -> None
        speichert die Komponente (Förderband) zu der umgeleitet werden soll
    """
    def __init__(self, vcscript):
        """
        Parameter
        - - - - -
        vcscript - module
        """
        # Funktionen und Eigenschaften der Oberklasse
        super(Transport, self).__init__()
        # Konstanten
        self.TYP = 'Transport'
        # Variablen
        app = vcscript.getApplication()
        komp = vcscript.getComponent()
        try:
            self.Anlage = app.findComponent('Schnittstelle').getProperty('Schnittstelle::Anlage').Value
        except:
            print('Komponente Schnittstelle bzw. dessen Eigenschaft Anlage fehlt!')
        self.App = app
        self.Komponente = komp
        self.Path = komp.findBehavioursByType(vcscript.VC_ONEWAYPATH)[0]
        if self.Path.Sensors:
            self.Sensor = self.Path.Sensors[0]
            self.Komp_signal =  self.Sensor.ComponentSignal
        # Importierte Funktionen
        self.resume = vcscript.resumeRun
        self.suspend = vcscript.suspendRun
        # Erstelle Verhaltensweisen, Eigenschaften und Verbindungen, falls notwendig
        self.konfig_komp(vcscript, komp)
        

    def OnStart(self):
        """Resette Attribute zu Simulationsbeginn und stelle Sensorposition (Frame) auf dem Pfad sicher.
        """
        # Kurvenförderer entfernt Sensor-Frame deswegen nochmal geprüft.
        # Kurvenförderer nicht duplizieren sondern einzeln ins Layout ziehen, sonst Veränderung der Path-Frames
        self.set_sensor_frame()
        # - Eigenschaften ud Methoden von Upvia
        self.reset_OnStart(self.App)
        # Init./Reset Eigenschaften
        self.Sensor_path_distanz = self.Sensor.Frame.FramePositionMatrix.P.X 
        self.Umleiten = None
        self.Sensor_weltpos = self.Komponente.PositionMatrix * self.Sensor.Frame.FramePositionMatrix
    
    def OnSignal(self, signal):
        """Aufgerufen wenn bei verbundenen Signalen der Wert sich verändert. 
        UpdateSignal
        - Funktionen
        real : 
        'umleiten' - Komponentenname
            leite die Komponenten auf dem Förderband zur bestimmten Komponente bzw. Förderband
        'erstelle' - Komponentenname
            erstelle bestimmte Komponente

        virtuell : 
        'signal' - /
            vergleicht reale und virtuelle Signale; erstellt Komponente falls notwendig
        
        ComponentSignal
        real : 
            sende Informationen zur Datenbank, dass eine Komponente am Sensor in der realen Anlage ist

        virtuell :
            vergleiche reale und virtuelle Signale und entferne Komponente falls notwendig

        Parameter
        - - - - -
        signal - vcStringSignal, vcComponentSignal
            StringSignal um Befehle über die Datenbank erhalten zu können und ComponentSignal zum signalisieren von erfassten
            Komponenten
        """
        # Funktion abh. von Signal und Signalwert ausgeführt
        if self.Anlage == 'virtuell':
            if signal.Name == 'UpdateSignal':
                update = literal_eval(signal.Value)
                if update['Funktion'] == 'signal':
                    self.vergleiche_virtuell(update['Info'], self.Path, self.Sensor_path_distanz, self.Sensor_weltpos)
            elif signal == self.Komp_signal:
                self.vergleiche_real(signal)
        elif self.Anlage == 'real':
            if signal.Name == 'UpdateSignal':
                update = literal_eval(signal.Value)
                if update['Funktion'] == 'umleiten':
                    self.update_umleite(update['Info'])
                elif update['Funktion'] == 'erstelle':
                    self.erstelle_komponente(update['Info'], self.Path, self.Sensor_weltpos)
            elif signal == self.Komp_signal and signal.Value:
                if signal.Value:
                    if self.Umleiten:
                        self.umleite_komp(signal.Value)
                    else:
                        self.update_db(self.Komponente.Name, self.TYP, 'signal', signal.Value.Name)
                else:
                    self.update_db(self.Komponente.Name, self.TYP, 'signal', '')

    def OnRun(self):
        pass

    def konfig_komp(self, vcscript, komp):
        """Erstellt notwendige Verhaltensweisen und Eigenschaften und verbindet die benötigten Signale mit diesem Script.
        
        Verhaltensweisen :
        'ComponentPathSensor' - vcBehaviour
            neuer Sensor wird erstellt, wenn keine im Path vorhanden ist
        'ComponentSignal' - vcComponentSignal
            neues Signal wird erstellt, wenn keine im Sensor ist
        'UpdateSignal' - vcStringSignal
            Signal zum Weiterreichen der Informationen aus der Datenbank

        Eigenschaften :
        'Schnittstelle::Typ' - vcString
            zum Kennzeichnen der Komponente für die Datenbank und Informationserfassung (UpdateSignal)
        
        Verbindungen mit diesem Script:
        'UpdateSignal'
        'ComponentSignal'

        Parameter
        - - - - -
        vcscript - module
        komp - vcComponente
            diese Komponente
        """
        # Referenz zum Pythonscript
        script = komp.findBehaviour('Script')
        # Verhaltensweisen
        if not self.Path.Sensors:
            sensor = komp.findBehavioursByType('ComponentPathSensor')
            if not sensor:
                self.Sensor = komp.createBehaviour(vcscript.VC_COMPONENTPATHSENSOR, 'ComponentPathSensor')
            else:
                self.Sensor = sensor
            self.Path.Sensors = [self.Sensor]
            self.set_sensor_frame()
        if not self.Sensor.ComponentSignal:
            komp_signal = komp.findBehaviour('ComponentSignal')
            if not komp_signal:
                self.Komp_signal = komp.createBehaviour(vcscript.VC_COMPONENTSIGNAL, 'ComponentSignal')
            else:
                self.Komp_signal = komp_signal
            self.Sensor.ComponentSignal = self.Komp_signal
        update_signal = komp.findBehaviour('UpdateSignal')
        if not update_signal:
            update_signal = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
        # Eigenschaften
        if not self.Komponente.getProperty('Schnittstelle::Typ'):
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP
        # Verbindungen
        if not script:
            print(self.Komponente.Name, 'Pythonscript in Script umbenennen und Layout neu laden.')
        else:
            signale = [self.Komp_signal, update_signal]
            for signal in signale:
                if script not in signal.Connections:
                    signal.Connections += [script]
    
    def set_sensor_frame(self):
        """Falls die Sensorposition nicht durch ein Frame festgelegt wurde, dann wird die mittlere Frame aus den Pfad-Frames
        als Sensorposition gewählt.
        """
        # Lege sensorposition auf Path fest
        if not self.Sensor.Frame:
            index_frame = int(len(self.Path.Path)/2)
            frame = self.Path.Path[index_frame]
            self.Sensor.Frame = frame

    def umleite_komp(self, komp):
        """Sende ein Signal an die zu umleitende Komponente, dass eine bestimmte Komponente erstellt werden soll.

        Parameter
        - - - - -
        komp - vcComponent
            die mit dem Sensor erfasste Komponente
        """
        # Sende ein Signal zum Fließband, zu der umgeleitet werden. Erstelle dort Komponente und entferne hier Komponente
        info = repr({'Funktion':'erstelle', 'Info': komp.Name})
        self.Umleiten.signal(info)
        komp.delete()

    def update_umleite(self, zu_komp):
        """Speichert das UpdateSignal der Komponente, zu der umgeleitet werden soll.
        
        Parameter
        - - - - - 
        zu_komp - vcStringSignal
            UpdateSignal der Komponente (Förderband), zu der die ankommenden Komponenten umgeleitet werden sollen
        """
        # Lege fest ob umgeleitet werden soll oder nicht und wohin und speichere die Info
        update = self.App.findComponent(zu_komp).findBehaviour('UpdateSignal')
        if update != self.Umleiten:
            self.Umleiten = update
        else:
            self.Umleiten = None

    

    

        


        

    
            
        
        



        
        
