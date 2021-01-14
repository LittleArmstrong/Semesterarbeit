from ast import literal_eval

class Feeder():
    def __init__(self, vcscript):
        # Konstanten
        self.TYP = 'Feeder'
        # Referenz zur Anwendung, der Komponente und dem Modul 
        self.App = vcscript.getApplication()
        self.Komponente = vcscript.getComponent()
        self.Vcscript = vcscript
        # Behaviours der Komponente
        self.Creator = self.Komponente.findBehaviour('ComponentCreator')
        self.Container = self.Komponente.getBehaviour('ComponentContainer')
        self.Update_signal = self.Komponente.getBehaviour('UpdateSignal')
        # Eigenschaften der Komponente
        self.Position = self.Komponente.WorldPositionMatrix
        self.Produkt = self.Komponente.getProperty('Schnittstelle::Produkt')
        # Erstelle die Eigenschaften und Behaviours, falls diese nicht existieren
        self.konfiguriere_komponente(vcscript)
        # Importierte Funktionen
        self.suspend = vcscript.suspendRun
        self.resume = vcscript.resumeRun
        self.delay = vcscript.delay

    def konfiguriere_komponente(self, vcscript):
        # Behaviours
        # - Creator: Zum erstellen von Komps
        if not self.Creator:
            self.Creator = self.Komponente.createBehaviour(vcscript.VC_COMPONENTCREATOR, 'ComponentCreator')
            self.Creator.getConnector('Output').connect(self.Container.getConnector('Input'))
        # - Container: Temporäre Aufbewahrung, um Position festlegen zu können
        if not self.Komponente.getBehaviour('ComponentContainer'):
            self.Komponente.createBehaviour(vcscript.VC_COMPONENTCONTAINER, 'ComponentContainer')
        # - UpdateSignal: Zum erhalten von Info und Befehlen
        if not self.Komponente.getBehaviour('UpdateSignal'):
            update_signal = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
            script = self.Komponente.getBehaviour('PythonScript')
            update_signal.Connections = [script]
        # Eigenschaften
        if not self.Komponente.getProperty('Schnittstelle::Typ'):
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP
        # - Produkt: Bestimmt welches Produkt hergestellt werden soll (Name). Produkt muss innerhalb Layout irgendwo platziert sein
        if not self.Produkt:
            self.Produkt = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Produkt')

    def OnStart(self):
        # Objekt-Eigenschaften
        self.Intervall = 0
        # - Path des Fließbandes
        self.Path = self.Komponente.findBehaviour('OutInterface').ConnectedComponent.findBehavioursByType(self.Vcscript.VC_ONEWAYPATH)[0]
        # Reset Creator, damit keine Komponenten erstellt werden
        self.Creator.Interval = 0
        self.Creator.Limit = 0
        # Lege die zu erstellende Komponente fest
        self.Creator.Part = self.App.findComponent(self.Produkt.Value).Uri

    def OnSignal(self, signal):
        # Lege Intervall fest und erstelle Komponente, falls direkt eine erstellt werden soll
        update = literal_eval(signal.Value)
        if update['Funktion'] == 'erstelle':
            self.erstelle_komponente()
        elif update['Funktion'] == 'intervall':
            self.set_intervall(int(update['Info']), False)
        elif update['Funktion'] == 'intervall_sofort':
            self.set_intervall(int(update['Info']), True)
            
    def set_intervall(self, intervall, sofort = False):
        # Lege intervall fest
        if intervall:
            if sofort:
                self.erstelle_komponente()
            self.Intervall = intervall
            self.resume()

    def OnRun(self):
        # Erstelle Komponente abh. vom festgelegten Intervall
        while True:
            if not self.Intervall:
                self.suspend()
            elif self.Intervall:
                # Erstelle und positioniere Komponente
                self.erstelle_komponente()
            self.delay(self.Intervall)
    
    def erstelle_komponente(self):
        # Erstelle Komponente, lege Position fest und platziere auf Path
        komp = self.Creator.create()
        komp.PositionMatrix = self.Position
        self.Path.grab(komp)
            
    
    
    

    


    