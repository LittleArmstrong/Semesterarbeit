from ast import literal_eval

class FeederKomponente():
    def __init__(self, vcscript):
        komp = vcscript.getComponent()
        oface = komp.findBehaviour('OutInterface')
        verbundene_komp = oface.ConnectedComponent

        self._app = vcscript.getApplication()

        self._creator = komp.findBehaviour('ComponentCreator')
        self._path = verbundene_komp.findBehaviour('One-WayPath__HIDE__') or verbundene_komp.findBehaviour('Path__HIDE__')
        self._container = komp.getBehaviour('_ComponentContainer')
        self._string_signal = komp.getBehaviour('_StringSignal')

        self.produkt = komp.getProperty('Produkt')

        self._konfiguriere_komp(vcscript, komp)

        self._creator_intervall = self._creator.getProperty('Interval')
        self._creator_limit = self._creator.getProperty('Limit')

        self._position = komp.PositionMatrix

        self.produkt.OnChanged = self._set_part

        self._set_part(self.produkt)
        
        self._suspend = vcscript.suspendRun
        self._resume = vcscript.resumeRun
        self._delay = vcscript.delay



    def OnStart(self):
        self._creator_intervall.Value = 0    
        self._creator_limit.Value = 0

    def OnRun(self):
        while True:
            if not self._creator_intervall.Value:
                self._suspend()
            self._delay(self._creator_intervall.Value)
            komp = self._creator.create()
            komp.PositionMatrix = self._position
            self._path.grab(komp)
            

    def OnSignal(self, signal):
        update = literal_eval(signal.Value)
        intervall = ''

        if type(update['Info']) == int:
            intervall = update['Info']
            self._creator_intervall.Value = intervall
            self._resume()

        if update['Funktion'] == 'erstelle' or (update['Funktion'] == 'intervall_direkt' and intervall):
            self._erstelle_komp()

    def _erstelle_komp(self):
        komp = self._creator.create()
        komp.PositionMatrix = self._position
        self._path.grab(komp)

    def _konfiguriere_komp(self, vcscript, komp):
        if not self._creator:
            self.creator = komp.createBehaviour(vcscript.VC_COMPONENTCREATOR, 'ComponentCreator')

        if not self._container:
            self._container = komp.createBehaviour(vcscript.VC_COMPONENTCONTAINER, '_ComponentContainer')

        if not self._string_signal:
            self._string_signal = komp.createBehaviour(vcscript.VC_STRINGSIGNAL, '_StringSignal')
            script = komp.getBehaviour('PythonScript')
            self._string_signal.Connections = [script]

        if not self.produkt:
            self.produkt = komp.createProperty(vcscript.VC_STRING, 'Produkt')

        creator_output = self._creator.getConnector('Output')

        if not creator_output.Connection:
            container_input = self._container.getConnector('Input')
            creator_output.connect(container_input)

    def _set_part(self, prop):
        if prop.Value and self._creator.Part != prop.Value:
            produkt = self._app.findComponent(prop.Value)
            uri = produkt.Uri
            self._creator.Part = uri