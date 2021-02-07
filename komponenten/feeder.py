#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ast import literal_eval

class Feeder():
    """ Quelle der Komponenten/Produkte. Script wurde für die Komponente 'Feeder Process' in 'Process Flow Components' im eCatalog 
    entwickelt. Zu erstellendes Produkt wird mit der Eigenschaft 'Schnittstelle::Produkt' erstellt. Das zu erstellende Produkt muss
    irgendwo im Layout platziert sein.
    Pythonscript namens 'Script':
    import vcScript
    from vccode import Feeder

    komptyp = Feeder(vcScript)

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
    App : vcApplication
        Referenz zur Anwendung
    Creator : vcComponentCreator
        Verhaltensweise 'ComponentCreator__HIDE__'
    Komponente : vcComponent
        diese Komponente
    Produkt : vcProperty
        die Eigenschaft 'Schnittstelle::Produkt' dieser Komponente
    Vcscript : module
        Modul vcScript
    
    Importierte Funktionen
    - - - - - - - - - - - -
    delay(zeit) -> None
        Stoppt die Ausführung des Scripts für bestimmte Zeit
    resume() -> None
        führt die Ausführung des OnRun-Event fort
    suspend() -> None
        stoppt die Ausführung des OnRun-Event

    Methoden
    - - - - -
    OnStart() -> None
        Event - 
    
    """
    def __init__(self, vcscript):
        # Konstanten
        self.TYP = 'Feeder'
        # Variablen
        komp = vcscript.getComponent()
        # Eigenschaften
        self.App = vcscript.getApplication()
        self.Creator = komp.findBehaviour('ComponentCreator__HIDE__')
        self.Komponente = komp
        self.Produkt = komp.getProperty('Schnittstelle::Produkt')
        self.Vcscript = vcscript
        # Erstelle Verhaltensweisen/Eigenschaften
        self.konfig_komp(vcscript)
        # Importierte Funktionen
        self.delay = vcscript.delay
        self.resume = vcscript.resumeRun
        self.suspend = vcscript.suspendRun
    
    def OnStart(self):
        """Resettet Attribute zum Startwert, bestimmt die Position, den Pfad und setzt das zu erstellende Produkt fest.

        Pfad ist Verhaltensweise der Komponente(Förderband) mit der der Feeder verbunden ist.
        """
        # Variabelen
        frame_pos = self.Komponente.findFeature('MainFrame').FramePositionMatrix
        komp_pos = self.Komponente.WorldPositionMatrix
        welt_pos = komp_pos * frame_pos
        # Eigenschaften
        self.Intervall = 0
        self.Path = self.Komponente.findBehaviour('ConveyorInterface').ConnectedComponent.findBehavioursByType(self.Vcscript.VC_ONEWAYPATH)[0]
        self.Position = welt_pos
        self.Update_produkt = None        
        # Lege die zu erstellende Komponente fest
        try:
            self.Creator.Part = self.App.findComponent(self.Produkt.Value).Uri
        except:
            print(self.Komponente.Name, 'Produkt im Layout nicht gefunden. Bitte stelle sicher, dass das Produkt im Layout vorhanden ist.')

    def OnSignal(self, signal):
        """Aufgerufen durch UpdateSignal.

        Funktionen :
        'erstelle'
            erstellt Produkt
        'intervall' :
            setzt das Intervall zwischen der Erstellung der Produkte fest
        'intervall_sofort' :
            Kombination aus Funktion 'erstelle' und 'intervall'

        Parameter
        - - - - -
        signal - vcStringSignal
            UpdateSignal, welches angibt wann Produkte erstellt werden sollen
        """
        # Lege Intervall fest und erstelle Komponente, falls direkt eine erstellt werden soll
        if signal.Name == 'UpdateSignal':
            update = literal_eval(signal.Value)
            if update['Funktion'] == 'erstelle':
                self.erstelle_komp()
            elif update['Funktion'] == 'intervall':
                self.set_intervall(int(update['Info']), False)
            elif update['Funktion'] == 'intervall_sofort':
                self.set_intervall(int(update['Info']), True)
    
    def OnRun(self):
        """Stellt Produkte her.

        Ist kein Intervall gegeben, so wird das OnRun-Event gestoppt und erst dann wieder fortgeführt, wenn im OnSignal eine Funktions-
        ausführung befehlt wurde.
        """
        # Erstelle Komponente abh. vom festgelegten Intervall
        while True:
            if not self.Intervall:
                self.suspend()
            elif self.Intervall:
                # Erstelle und positioniere Komponente
                self.erstelle_komp()
            self.delay(self.Intervall)
    
    def erstelle_komp(self):
        """Erstellt ein Produkt.
        """
        # Erstelle Komponente, lege Position fest und platziere auf Path
        komp = self.Creator.create()
        komp.PositionMatrix = self.Position
        self.Path.grab(komp)
        
    def konfig_komp(self, vcscript):
        """Erstellt Verhaltensweisen/Eigenschaften und verbindet Signale mit diesem Script.

        Verhaltensweisen :
        'ComponentCreator__HIDE__' - vcComponentCreator
            zum Erstellen von Produkten
        'ComponentContainer__HIDE__' - vcComponentContainer
            zur temporären Aufbewahrung der Produkte, damit deren Position festgelegt werden kann
        'UpdateSignal - vcStringSignal
            zum Erhalten der Informationen aus der Datenbank
        
        Eigenschaften :
        'Schnittstelle::Typ' - vcString
            zum Kennzeichnen der Komponente für die Datenbank und Informationserfassung (UpdateSignal)
        'Schnittstelle::Produkt' - vcString
            Produkt, das erstellt werden soll

        Verbindugen mit diesem Script :
        'UpdateSignal'

        Verbindungen zwischen Verhaltensweisen :
        'ComponentCreator__HIDE__' Output -> Input 'ComponentContainer__HIDE__'

        Verhaltensweisen, die entfernt werden:
        'ProcessExecutor__HIDE__'
        'ProductCreator'

        Parameter
        - - - - - 
        vcscript - module
            Module vcScript
        """
        # Referenz zum PythonScript
        script = self.Komponente.findBehaviour('Script')
        if not script:
            print(self.Komponente.Name,'Pythonscript in Script umbenennen und Layout neu laden.')
        # Verhaltensweisen
        # - Creator: Zum erstellen von Komps
        if not self.Creator:
            self.Creator = self.Komponente.createBehaviour(vcscript.VC_COMPONENTCREATOR, 'ComponentCreator__HIDE__')
            self.Creator.Interval = 0
            self.Creator.Limit = 0
        # - Container: Temporäre Aufbewahrung, um Position festlegen zu können
        container = self.Komponente.findBehaviour('ComponentContainer__HIDE__')
        if not container:
            container = self.Komponente.createBehaviour(vcscript.VC_COMPONENTCONTAINER, 'ComponentContainer__HIDE__')
        # - UpdateSignal: Zum erhalten von Info und Befehlen
        update_signal = self.Komponente.findBehaviour('UpdateSignal')
        if not update_signal:
            update_signal = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
        # Eigenschaften
        if not self.Komponente.getProperty('Schnittstelle::Typ'):
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP
        # - Produkt: Bestimmt welches Produkt hergestellt werden soll (Name). Produkt muss innerhalb Layout irgendwo platziert sein
        if not self.Produkt:
            self.Produkt = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Produkt')
        # Verbindungen zwischen Verhaltensweisen
        # - Verbinde UpdateSignal mit Script
        if not script:
            print(self.Komponente.Name, 'Pythonscript in Script umbenennen und Layout neu laden.')
        elif script not in update_signal.Connections:
            update_signal.Connections = [script]
        # - Verbinde Creator-Output mit Container-Input
        creator_output = self.Creator.getConnector('Output')
        if not creator_output.Connection:
            creator_output.connect(container.getConnector('Input'))
        # Entferne störende Verhaltensweisen
        executor = self.Komponente.findBehaviour('ProcessExecutor__HIDE__')
        if executor:
            executor.delete()
        pcreator = self.Komponente.findBehaviour('ProductCreator')
        if pcreator:
            pcreator.delete()

    def set_intervall(self, intervall, sofort = False):
        """Legt Zeitintervall zwischen der Produktion von Produkten fest.
        Parameter
        - - - - -
        intervall - int
            Zeitintervall zwischen der Produktion von Produkten
        sofort=False - bool, optional
            sofort Produkt erstellen und dann nach Zeitintervall
        """
        # Lege intervall fest
        if intervall:
            if sofort:
                self.erstelle_komp()
            self.Intervall = intervall
            self.resume()
        else:
            self.suspend()
    

    
            
    

    
    
    
            
    
    
    

    


    