#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .upvia import Upvia
from ast import literal_eval
from datenbank import Datenbank

class Roboter():
    """ Klasse für die Robotersteuerung eines Sechsarm-Roboter. 
    Pythonscript namens 'Script' mit folgendem Inhalt erstellen:
    import vcScript
    import vcHelpers.Robot2 as vcRobot
    from vccode import Roboter

    komptyp = Roboter(vcScript, vcRobot)

    def OnStart():
        komptyp.OnStart()
    
    def OnSignal(signal):
        komptyp.OnSignal(signal)
    
    def OnRun():
        komptyp.OnRun()

    Attribute:
    - - - - - - 
    TYP : str
        Konstante zum Kennzeichnen der Komponente für die Steuerung (GUI) und Datenbank
    Anlage : str
        ob real oder virtuell; bestimmt die Funktionen der Komponenten
    Auto : bool
        ob Roboter automatisch oder manuell gesteuert werden soll
    Container : vcContainer
        Referenz zur Verhaltensweise 'GraspContainer'
    Creator : vcComponent
        Referenz zur Komponente 'Creator' 
    Gelenke : list
        Liste mit Gelenkwerten
    Greifen : int
        in welcher Station eine Komponente gegriffen werden soll (manuell)
    Komp_im_Greifer : vcComponent
        die Komponente im Greifcontainer
    Name : str
        Name der Komponente
    Path : vcMotionPath
        Referenz zur Verhaltensweise 'Path__HIDE__'
    Platzieren : int
        in welcher Station Komponente platziert werden soll (manuell)
    Roboter : vcHelpers.Robot.vcRobot
        vcRobot-Objekt zur einfacheren Steuerung des Roboters über Python
    Ruhe_pos : list
        Liste mit gelenkwerten für die Ruheposition
    Stationen : list
        Liste aus Wörterbücher mit Informationen über die zu besuchenden Stationen
    Vcrobot : module
        Referenz zum Modul vcHelpers.Robot2;
    Vcscript : module
        Referenz zum Modul vcScript
    
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
    OnStart()
        Event - resettet bzw. initialisiert Attribute, die sich zwischen Simulationsstart ändern (können)
    OnSignal(signal)
        Event - führt Funktionen abh. vom Signal und dessen Wert aus
    OnRun()
        Event - Hauptfunktion die während der Simulation ausgeführt wird
    auto_ablauf()
        sorgt für das automatische Greifen und Platzieren von Komponenten von Station zu Station
    check_belegung(index)
        untersucht ob eine Komponente auf der Station ist oder nicht
    check_komp(name)
        erstellt oder entfernt Komponente im Greifcontainer
    check_stationen()
        ermittelt die Stationen zu der die Komponente mit diesem Roboter transportiert wird
    greife(iStation, komp) 
        greift die Komponente auf der jeweiligen Station, wenn die Bedingungen es erlauben
    konfig_komp(vcscript, komp)
        erstellt notwendige Verhaltensweisen, Eigenschaften und verbindet die Signale mit diesem Script
    platziere(iStation, next_komp)
        platziere die Komponente im Greifcontaiiner auf die Station, wenn die Bedingungen es erlauben
    update_gelenke(update)
        speichert die Ziel-Gelenkwerte im Attribut Gelenke vom UpdateSignal
    update_manuell(update)
        speichert die nächste manuelle Bewegung (Greifen/Platzieren) und die ZielStation
    verwalte_signale(signal_map, port, bool_wert)
        wird bei Änderung des Inputs aufgerufen und sorgt für die Weiterführung des OnRun-Events
    zu_maschine(station, komp, move, container=None)
        regelt den Bewegungsablauf des Roboters zum Greifen oder Platzieren von Komponenten in einer Maschine
    zu_transport(komp, station=None)
        regelt den Bewegungsablauf des Roboters zum Greifen oder Platzieren von Komponenten auf einem Fließband
    """
    def __init__(self, vcscript, vcrobot):
        """
        Parameter
        - - - - - 
        vcscript : module
            vcScript-Modul
        vcrobot : module
            vcHelpers.Robot2-Modul
        """
        # Konstante
        self.TYP = 'Roboter'
        # Referenz zur Anwendung und Komponente
        app =  vcscript.getApplication()
        komp = vcscript.getComponent()
        # Eigenschaften
        try:
            self.Anlage = app.findComponent('Schnittstelle').getProperty('Schnittstelle::Anlage').Value
        except:
            print('Komponente Schnittstelle bzw. dessen Eigenschaft Anlage fehlt!')
        self.Ruhe_pos = [0,0,90,0,0,0]
        self.Vcrobot = vcrobot
        self.Vcscript = vcscript
        # Importierte Funktionen 
        self.resume = vcscript.resumeRun
        self.suspend = vcscript.suspendRun
        if self.Anlage == 'real':
            # Eigenschaften
            self.Name = komp.Name
            self.Stationen = []
            # Importierte Funktion
            self.update_db = Upvia().update_db
        else:
            # Eigenschaften
            self.Container = komp.findBehaviour('GraspContainer')
            self.Creator = app.findComponent('Creator')
            self.Path = komp.findBehaviour('Path__HIDE__')
        # Verhaltensweisen und Eigenschaften erstellen, falls notwendig
        self.konfig_komp(vcscript, komp)

    def OnStart(self):
        """ Attributwerte werden beim Starten der Simulation resettet und die Stationen, die durchlaufen werden sollen, ermittelt.
        """
        # Reset/Init. von Eigenschaften: virtuell und real
        self.Gelenke = self.Ruhe_pos
        self.Roboter = self.Vcrobot.getRobot()
        # Reset/Init. von Eigenschaften
        if self.Anlage == 'real':
            self.check_stationen()
            # Eigenschaften
            self.Auto = True
            self.Greifen = None
            self.Komp_im_greifer = None
            self.Platzieren = None
            # Event
            self.Roboter.SignalMapIn.OnSignalTrigger = self.verwalte_signale
        
    def OnSignal(self, signal):
        """Aufgerufen wenn bei verbundenen Signalen der Wert sich verändert. 
        StringSignal namens UpdateSignal überreicht Informationen zur Ausführung von Funktionen.

        Der Signalwert ist ein Wörterbuch mit den Indizes 'Funktion' und 'Info' im String-Format, 
        welche über literal_ast in ein Wörterbuch-Format umgewandelt wird.

        Der Index 'Funktion' hat folgende mögliche Werte: 
            reale Anlage : 'auto', 'greifen', 'platzieren', 'bewegeGelenk', 'bewegeGelenk+'
            virtuelle Anlage : 'gelenke', 'komp'

        Funktionen : 
        real
        'auto' - keine zusätlichen Info
            schaltet zwischen automatischer und manueller Steuerung um; bei jeder anderen Funktion
            wird automatisch auf manuell umgeschaltet
        'greifen' - int
            Ganzzahlwert legt fest, von welcher Station eine Komponente aufgehoben werden soll,
            falls vorhanden; 1 für erste Station, 2 für zweite etc.
        'platzieren' - int
            wie 'greifen', nur dass eine Komponente platziert wird
        'bewegeGelenk' - list
            Liste aus Gelenkwerten, zu der sich der Roboter absoult bewegen soll
        'bewegeGelenk+' - list
            wie 'bewegeGelenk', nur relativ

        virtuell
        'gelenke' - list
            wie 'bewegeGelenke'
        'komp' - str
            Info ist Name der Komponente die erstellt und in das Greifcontainer hinzugefügt werden soll;
            bei leerem String wird die Komponente stattdessen entfernt

        Parameter
        - - - - - 
        signal : vcSignal, vcStringSignal
            Signal, dessen Wert sich verändert hat und deshalb dieses Event aufgerufen hat
        """
        if signal.Name == 'UpdateSignal':
            update = literal_eval(signal.Value)
            if self.Anlage == 'real':
                if update['Funktion'] == 'auto':
                    self.Auto = not self.Auto
                    self.resume()
                else:
                    self.Auto = False 
                if update['Funktion'] == 'greifen' or update['Funktion'] == 'platzieren':
                    self.update_manuell(update)
                elif update['Funktion'] in 'bewegeGelenk+':
                    self.update_gelenke(update)
            elif self.Anlage == 'virtuell':
                if update['Funktion'] == 'komp':
                    self.check_komp(update['Info'])  
                    
    def OnRun(self):
        """ Untersuche die Attribute und führe jeweilge Funktion durch, falls dessen Wert nicht None ist.

        Das OnRun-Event wird gestoppt und erst dann fortgeführt, wenn das OnSignal-Event aufgerufen wird, nachdem
        das jeweilige Attribut aktualisiert wurde. Dann werden die jeweiligen Attribute geprüft und abh. vom Wert
        eine bestimmte Funktion ausgeführt.

        Zu überprüfende Attribute und die Funktionen :
        real : 
        Gelenke - Bewege Roboter bis Zielgelenkwerte erreicht wurden
        Auto - Automatisches Greifen und PLatzieren der Komponente zu den Stationen entlang der Route falls True
        Greifen - Greife Komponente auf spezifizierter Station, falls möglich
        Platzieren - Platziere Komponente auf spezifizierter Station, falls möglich
        """
        while True:
            self.suspend()
            if self.Anlage == 'real':
                if self.Gelenke:
                    self.Roboter.driveJoints(*self.Gelenke)
                    self.Gelenke = None
                if self.Auto:
                    self.auto_ablauf()
                if self.Greifen:
                    iStation, komp = self.check_belegung(self.Greifen-1)
                    self.greife(iStation, komp)
                if self.Platzieren:
                    iStation, komp = self.check_belegung(self.Platzieren-1)
                    self.platziere(iStation, komp)

    def auto_ablauf(self):
        """ Überprüft die Stationen in umgekehrter Reihenfolge beginnend bei der vorletzten Station und überprüft die Komponentenbelegung
            in der gewählten und der danach (in richtiger Reihenfolge) kommenden Station und führt je nachdem Greif- oder Platzier-Befehle
            aus.

            Bei einer Maschine wird auch überprüft, ob die Türen offen sind.

        """
        # Regelt automatischen Ablaufs des Roboters 
        for i in range(len(self.Stationen) -2, -1, -1):
            if not self.Auto:
                break
            iStation, komp = self.check_belegung(i)
            next_iStation, next_komp = self.check_belegung(i+1)
            if komp and not next_komp:
                if next_iStation['Typ'] == 'Maschine' and not next_iStation['Offen'].Value:
                    continue
                self.greife(iStation, komp)
                self.platziere(next_iStation, next_komp)
    
    def check_belegung(self, index):
        """ Prüft die jeweilige Station auf Komponentenbelegung und gibt die Komponenten sowie ein Wörterbuch mit Informationen zur 
        Station zurück.

        Parameter
        - - - - - 
        index - int
            gibt die jeweilige Station an, die überprüft werden soll

        Rückgabe
        - - - - -
        iStation - dict
            Wörterbuch, das Info/Referenzen zur Station selbst, dessen Container/Signal und Typ hat
        """
        # Prüft ob Komponente in Maschine
        iStation = self.Stationen[index]
        if iStation['Typ'] == 'Maschine':
            komp = iStation['Container'].Components
        elif iStation['Typ'] == 'Transportstelle':
            komp = iStation['Signal'].Value
        return iStation, komp
    
    def check_komp(self, name):
        """ Erstellt oder Entfernt Komponente im Greifcontainer.

        Die zu erstellende Komponente wird über eine ComponentCreator-Verhaltensweise der Komponente 'Creator' erstellt
        und über eine Path-Verhaltensweise (RetainOffset=False) aufgefangen, welche dann im Greifcontainer abgelegt wird.

        Path-Verhaltensweise wird genutzt, um die Position des Containers nicht immer neu berechnen zu müssen.

        Parameter
        - - - - - 
        name - str
            Name der Komponente, die erstellt bzw. entfernt werden soll, falls String leer
        """
        # Erstellt/Entfernt Komp im Griff (virtuell)
        if name:
            if self.Container.Components:
                self.Container.Components[0].delete()
            komp = self.Creator.findBehaviour(name+'__HIDE__').create()
            self.Path.grab(komp)
        elif self.Container.Components:
            self.Container.Components[0].delete()

    def check_stationen(self):
        """ Ermittle die zu durchlaufenden Stationen.

        Stationen werden über ein BoolSignal mit dem Input des Roboters verbunden. Dafür stehen die Ports 150 bis 150 zur
        Verfügung. Stationen, die mit anderen Ports verbunden sind, werden ignoriert.

        Eine Maschine wird über das BoolSingal 'To_PLC_DoorIsOpen' mit dem Roboter verbunden.
        Eine Transportstelle wird über das BoolSignal, welches mit dem ComponentPathSensor verbunden ist, verbunden.
        
        Für jede Station wird ein Wörterbuch gespeichert, welches folgende Informationen enthält:
        Transportstelle und Maschine : 
        'Station' : vcComponent
            Referenz zur Station (Komponente) selbst
        'Typ' : 'Maschine' oder 'Transportstelle'
            gibt an, um was für eine Station es sich handelt

        Maschine : 
        'Container' : vcContainer
            Referenz zur Verhaltensweise 'ProcessContainer'; zum Prüfen, ob eine Komponente vorhanden ist oder nicht
        'Offen' : vcBoolSignal
            Referenz zur Verhaltensweiser 'TO_PLC_DoorIsOpen'; zum Prüfen, ob die Tür offen ist oder nicht

        Transportstelle :
        'Signal' :  vcComponentSignal
            Referenz zur Verhaltensweise 'SensorComponentSignal'; zum Prüfen, ob eine Komponente vorhanden ist oder nicht
        """
        # Ermittle zu durchlaufende Stationen (Macshine/Transportstelle)
        ports = self.Roboter.SignalMapIn.getAllConnectedPorts()
        for port in ports:
            # Port 150 bis 159 für  Stationen reserviert
            if not (150 <= port < 160):
                continue
            station = self.Roboter.SignalMapIn.getConnectedExternalSignals(port)[0].Component
            typ = station.getProperty('Schnittstelle::Typ').Value
            if typ == 'Maschine':
                offen = station.findBehaviour('TO_PLC_DoorIsOpen')
                container = station.findBehaviour('ProcessContainer__HIDE__')
                iStation = {'Station':station,'Typ': typ, 'Container': container, 'Offen': offen}
            elif typ == 'Transportstelle':
                signal = station.findBehaviour('SensorComponentSignal')
                iStation = {'Station':station,'Typ': typ, 'Signal':signal}
            self.Stationen.append(iStation)
    
    def greife(self, iStation, komp):
        """ Greife Komponente in ausgewählter Station.

        Prüft zuerst, ob eine Komponente vorhanden ist und keine im Greifer. Dann wird der Typ der Station ('Maschine' oder 'Transportstelle')
        geprüft und abh. davon die notwendigen Bewegungen ermittelt.

        Bei der Maschine wird zusätzlich noch geprüft, ob die Türen offen sind.

        War das Greifen erfolgreich und liegt eine Komponente im Greifcontainer, so wird die Datenbank aktualisiert.

        Parameter
        - - - - - 
        iStation - dict
            Wörterbuch mit Informationen zur Station
        komp - vcComponent
            Referenz zur Komponenten, die gegriffen werden soll
        """
        # Greife Komponente
        if komp and not self.Komp_im_greifer:
            if iStation['Typ'] == 'Transportstelle':
                self.zu_transport(komp)
                self.Komp_im_greifer = komp
            elif iStation['Typ'] == 'Maschine':
                if iStation['Offen'].Value:
                    self.zu_maschine(iStation['Station'],  komp[0], 'greifen')
                    self.Komp_im_greifer = komp[0]
            if self.Komp_im_greifer:
                self.update_db(self.Name, self.TYP, 'komp', self.Komp_im_greifer.Name)
            self.Greifen = 0
            self.Roboter.driveJoints(*self.Ruhe_pos)
    
    def konfig_komp(self, vcscript, komp):
        """ Erstelle notwendige Verhaltensweisen und Eigenschaften, damit die Funktionen ordnungsgemäßt ausgeführt werden können.

        Verhaltensweisen :
        'UpdateSignal' - vcStringSignal
            zum weiterreichen der Informationen aus der Datenbank
        
        real :
        'UpdateScript' - vcScript
            zum Aktualisieren der Datenbank mit Gelenkwerten des realen Roboters
        
        virtuell :
        'Path__HIDE__' - vcMotionPath
            zum Weiterleiten der zu erstellten Komponente zum GreifContainer an richtiger Position
        
        Eigenschaften :
        'Schnittstelle::Typ' - vcString
            zum Kennzeichnen der Komponente für die Datenbank und Informationserfassung (UpdateSignal)
        
        Zuletzt werden notwendige Signale mit dem Script verbunden :
        'UpdateSignal'

        Parameter
        - - - - - 
        vcscript - vcScript
            Referenz zum Modul vcScript
        komp - vcComponent
            Referenz zur Komponente (Roboter)
        """
        # Erstelle notwendige Verhaltensweisen/Eigenschaften
        script = komp.findBehaviour('Script')
        # Verhaltensweisen
        update_signal = komp.findBehaviour('UpdateSignal')
        if not update_signal:
            update_signal = komp.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
        if self.Anlage == 'virtuell':
            if not self.Path:
                self.Path = komp.createBehaviour(vcscript.VC_ONEWAYPATH, 'Path__HIDE__')
                container_in = self.Container.getConnector('Input')
                self.Path.getConnector('Output').connect(container_in)
            update_script = komp.findBehaviour('UpdateScript')
            if update_script:
                update_script.delete()
        # Eigenschaften
        if not komp.getProperty('Schnittstelle::Typ'):
            typ = komp.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP
        # Verbindungen
        if not script:
            print(self.Name, 'Pythonscript in Script umbenennen und Layout neu laden.')
        elif script not in update_signal.Connections:
            update_signal.Connections += [script]
    
    def platziere(self, iStation, komp):
        """ Platziere Komponente in ausgewählter Station.

        Prüft zuerst, ob eine Komponente vorhanden ist und eine im Greifer. Dann wird der Typ der Station ('Maschine' oder 'Transportstelle')
        geprüft und abh. davon die notwendigen Bewegungen ermittelt.

        Bei der Maschine wird zusätzlich noch geprüft, ob die Türen offen sind.

        War das Platzieren erfolgreich und liegt keine Komponente im Greifcontainer, so wird die Datenbank aktualisiert.

        Parameter
        - - - - - 
        iStation - dict
            Wörterbuch mit Informationen zur Station
        komp - vcComponent
            Referenz zur Komponente in der Station
        """
        # Platziere Komponente
        if self.Komp_im_greifer and not komp:
            if iStation['Typ'] == 'Transportstelle':
                self.zu_transport(self.Komp_im_greifer, iStation['Station'])
                self.Komp_im_greifer = None
            elif iStation['Typ'] == 'Maschine' and iStation['Offen'].Value:
                self.zu_maschine(iStation['Station'], self.Komp_im_greifer, 'platzieren', iStation['Container'])
                self.Komp_im_greifer = None
            if not self.Komp_im_greifer:
                self.update_db(self.Name, self.TYP, 'komp', '')
            self.Platzieren = 0
            self.Roboter.driveJoints(*self.Ruhe_pos)
        
    def update_gelenke(self, update):
        """Die erhaltenen Gelenkwerte werden von String in Integer umgewandelt und zusammen mit der Info, ob es sich um
        relative oder absolute Werte handelt, gespeichert.

        Parameter
        - - - - - 
        update - dict
            enthält die Gelenkwerte und ob die Gelenkte relativ oder absolut bewegt werden sollen
        """
        # Speichert Gelenkwerte
        relativ = False
        gelenke = []
        werte = literal_eval(update['Info'])
        if update['Funktion'] == 'bewegeGelenk+':
            relativ = True
        gelenke += [int(wert) for wert in werte] + [0, relativ]
        self.Gelenke = gelenke
        self.resume()
    
    def update_manuell(self, update):
        """Speichert die Bewegung (greifen oder platzieren) die ausgeführt werden soll und die Station.

        Parameter
        - - - - - 
        update : dict
            Wörterbuch mit Funktion 'greifen' oder 'platzieren' und Info zur Station
        """
        # Speichert nächste manuelle Bewegung
        station_index = int(update['Info'])
        if 0 <= station_index <= len(self.Stationen):
            if update['Funktion'] == 'platzieren':
                self.Platzieren = station_index
            elif update['Funktion'] == 'greifen':
                self.Greifen = station_index
            self.resume()

    def verwalte_signale(self, signal_map, port, bool_wert):
        """ Die verbundenen Signale mit dem Roboter werden positiv, wenn eine Komponente an eine Transportstelle gelangt oder
        die Maschinentür auf ist. Dann wird das OnRun-Event forgeführt.

        Parameter
        - - - - - 
        signal_map : vcBooleanSignalMap
            Objekt mit allen Input-Ports und deren Werte
        port : int
            der Port, dessen Wert sich verändert hat und diese Funktion aufgerufen hat
        bool_wert : bool
            den Wert, den der Port angenommen 
        """
        # Signale: Komp angekommen, Maschinentür offen
        if bool_wert:
            self.resume()
    
    def zu_maschine(self, station, komp, move, container=None):
        """Die Bewegungen zur Komponente in der Maschine und das Greifen/Platzieren der Komponente wird hier definiert.

        Zur Bewegung werden folgende Frames zur Hilfe genommen:
        'ProductLocationApproach'
        'ProcessLocation'.

        Der Frame 'ProcessLocation' wird von selbst erstellt. Dieser ist an der gleichen Stelle wie der Frame 'ProductLocation', nur
        dass dieser im Root-Feature des Root-Node ist.

        Parameter
        - - - - - 
        station : vcComponent
            Referenz zur Station (Komponente)
        komp : vcComponent
            Referenz zur ergreifenden/platzierenden Komponente
        move : str
            Bewegung (Greifen/Glatzieren) das ausgeführt werden soll
        container=None : vcContainer
            Container der Station, in der die Komponente platziert werden soll; nur bei Platzierung notwendig
        """
        # Bewegung zur Prozessstelle der Maschine
        abstand = komp.BoundCenter.length()*2
        self.Roboter.jointMoveToComponent(station, ToFrame = 'ProductLocationApproach')
        self.Roboter.jointMoveToComponent(station, Tz=abstand, ToFrame = 'ProcessLocation')
        if move == 'greifen':
            self.Roboter.graspComponent(komp)
        elif move == 'platzieren':
            self.Roboter.releaseComponent(container)

    def zu_transport(self, komp, station = None):
        """Hier wird die Bewegung zum Förderband bzw. zur Transportstelle die i.d.R. auf dem Förderband ist definiert.

        Wird kein Argument für die Station gegeben, dann wird ein Greifvorgang ausgeführt.
        Wird ein Argument für die Station gegeben, dann wird ein Platziervorgang ausgeführt.

        Parameter
        - - - - - 
        komp - vcComponent
            zu ergreifende/platzierende Komponente
        station=None - vcComponent
            die Station auf der die Komponente platziert werden soll; wenn None, dann Greifvorgang
        """
        # Bewegung zum Fließband
        height = komp.BoundCenter.length() * 2
        if not self.Anlage=='real':
            return
        if not station:
            height=0
        self.Roboter.jointMoveToComponent(station or komp, Tz=200+height , OnFace='top')
        self.Roboter.linearMoveToComponent(station or komp, Tz=height, OnFace='top')
        if station:
            self.Roboter.releaseComponent(station)
        elif komp:
            self.Roboter.graspComponent(komp)
        self.Roboter.delay(0.1)
        self.Roboter.moveAway()


                    

            

   