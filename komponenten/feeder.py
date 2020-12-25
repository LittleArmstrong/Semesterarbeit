from ast import literal_eval

class Feeder():
    def __init__(self, vcscript):
        # Konstanten
        self.TYP = 'Feeder'

        # Referenz zur Anwendung und der Komponente selbst
        self.App = vcscript.getApplication()
        self.Komponente = vcscript.getComponent()
        
        # Behaviours der Komponente
        self.Creator = self.Komponente.findBehaviour('ComponentCreator')
        self.Container = self.Komponente.getBehaviour('ComponentContainer')
        self.Update_signal = self.Komponente.getBehaviour('UpdateSignal')

        # Eigenschaften der Komponente
        self.Position = self.Komponente.WorldPositionMatrix
        self.Produkt = self.Komponente.getProperty('Schnittstelle::Produkt')

        # Eigenschaften des Objekts
        self.Intervall = 0

        # Erstelle die Eigenschaften und Properties, falls diese nicht existieren
        self.konfiguriere_komponente(vcscript)

        # Importierte Funktionen
        self.suspend = vcscript.suspendRun
        self.resume = vcscript.resumeRun
        self.delay = vcscript.delay

        # Behaviours und Eigenschaften anderer Komponenten
        self.Verbundene_komponente = None
        self.Verbundener_path = None

        # Wertzuweisungen
        self.Creator.getProperty('Interval').Value = 0
        self.Creator.getProperty('Limit').Value = 0

    
    def OnStart(self):
        # Resettet das Erstellungsintervall und
        self.Intervall = 0
        self.set_part(self.Produkt)
        self.get_path()
        #print(t.P.X, t.P.Y, t.P.Z)
        #print(self.Position.P.X, self.Position.P.Y, self.Position.P.Z)

    def OnRun(self):
        # Erstelle Komponente abh. vom festgelegten Intervall
        while True:
            if not self.Intervall:
                self.suspend()
            elif self.Intervall:
                komp = self.Creator.create()
                komp.PositionMatrix = self.Position
                self.Verbundener_path.grab(komp)
            self.delay(self.Intervall)
            
    def OnSignal(self, signal):
        # Lege Intervall fest und erstelle Komponente, falls direkt eine erstellt werden soll
        update = literal_eval(signal.Value)
        intervall = ''

        if type(update['Info']) == int:
            intervall = update['Info']
            self.Intervall = intervall
            self.resume()

        if update['Funktion'] == 'erstelle':
            self.erstelle_komponente()
        elif update['Funktion'] == 'intervall_direkt' and intervall:
            self.erstelle_komponente()
    
    def konfiguriere_komponente(self, vcscript):
        # Behaviours
        if not self.Creator:
            self.Creator = self.Komponente.createBehaviour(vcscript.VC_COMPONENTCREATOR, 'ComponentCreator')

        if not self.Komponente.getBehaviour('ComponentContainer'):
            self.Komponente.createBehaviour(vcscript.VC_COMPONENTCONTAINER, 'ComponentContainer')

        if not self.Komponente.getBehaviour('UpdateSignal'):
            update_signal = self.Komponente.createBehaviour(vcscript.VC_STRINGSIGNAL, 'UpdateSignal')
            script = self.Komponente.getBehaviour('PythonScript')
            update_signal.Connections = [script]

        # Eigenschaften
        if not self.Komponente.getProperty('Schnittstelle::Typ'):
            typ = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Typ')
            typ.Value = self.TYP

        if not self.Produkt:
            self.Produkt = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Produkt')

        # Verbindungen
        if not self.Creator.getConnector('Output').Connection:
            container_input = self.Container.getConnector('Input')
            creator_output = self.Creator.getConnector('Output')
            creator_output.connect(container_input)

                
    def set_part(self, produkt):
        # Zu erstellendes Produkt festlegen
        if produkt.Value and self.Creator.Part != produkt.Value:
            zu_erstellende_komponente = self.App.findComponent(produkt.Value)
            uri = zu_erstellende_komponente.Uri
            self.Creator.Part = uri

    def get_path(self):
        # Referenz zum Path-Behaviour erhalten
        verbundene_komponente = self.Komponente.findBehaviour('OutInterface').ConnectedComponent\
             or self.Komponente.findBehaviour('ConveyorInterface').ConnectedComponent
        if self.Verbundene_komponente != verbundene_komponente or not self.Verbundener_path:
            self.Verbundene_komponente = verbundene_komponente
            self.Verbundener_path = verbundene_komponente.findBehaviour('One-WayPath__HIDE__') or verbundene_komponente.findBehaviour('Path__HIDE__')

    def erstelle_komponente(self):
        # Erstelle Komponente, lege Position fest und platziere auf Path
        erstellte_komponente = self.Creator.create()
        erstellte_komponente.PositionMatrix = self.Position
        self.Verbundener_path.grab(erstellte_komponente)


    