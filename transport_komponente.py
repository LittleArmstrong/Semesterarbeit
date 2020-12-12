from datenbank import Datenbank
from ast import literal_eval

class TransportKomponente():
    def __init__(self, vcscript, anlage):
        komp = vcscript.getComponent()
        komp_pos = komp.PositionMatrix
        sensor = komp.findBehaviour('ComponentPathSensor')
        
        self._app = vcscript.getApplication()
        self._komp = komp
        self._name = komp.Name
        self._anlage = anlage
        self._sensor_position_welt = komp_pos * sensor.Frame.FramePositionMatrix

        self._komp_signal = komp.findBehaviour('SensorSignal')
        self._creator = komp.findBehaviour('_ComponentCreator')
        self._container = komp.findBehaviour('_ComponentContainer')
        self._path = komp.findBehaviour('One-WayPath__HIDE__') or komp.findBehaviour('Path__HIDE__')

        self._konfiguriere_behaviours(vcscript, komp)

        self._real_signal = komp.getProperty('_Signal_real')

        self._part = self._creator.getProperty('Part')
        self._creator_intervall = self._creator.getProperty('Interval')
        self._creator_limit = self._creator.getProperty('Limit')
        self._retain_offset = self._path.getProperty('RetainOffset')

        self.produkt = komp.getProperty('Produkt')

        self._konfiguriere_properties(vcscript, komp)
        self._konfiguriere_verbindungen()

        self._sensor_distanz = komp.getProperty('SensorPosition').Value * self._path.PathLength

        
        self._part.OnChanged = self._set_part
        self._set_part(self.produkt)

    def OnStart(self):
        self._real_signal.Value = 0
        self._creator_intervall.Value = 0
        self._creator_limit.Value = 0
        self._retain_offset.Value = False

    def OnSignal(self, signal):
        if signal == self._komp_signal and signal.Value:
            if self._anlage == 'real':
                self._update_werte()
            elif self._anlage == 'virtuell' and not self._real_signal.Value:
                komp = signal.Value
                komp.delete()
        elif signal == self._komp_signal and not signal.Value and self._real_signal.Value:
            self._erstelle_komponente_am_sensor()
            self._entferne_erste_komponente_vor_sensor()

    def OnRun(self):
        pass

    def _erstelle_komponente_am_sensor(self):
        komp = self._creator.create()
        komp.PositionMatrix = self._sensor_position_welt
        self._path.grab(komp)

    def _entferne_erste_komponente_vor_sensor(self):
        komps = self._path.Components
        if komps:
            komps_distanz = [self._sensor_distanz - komp.getPathDistance() for komp in komps]
            index_erste_komp_vor_sensor = komps_distanz.index(min([distanz for distanz in komps_distanz if distanz > 0]))
            komp_vor_sensor = komps[index_erste_komp_vor_sensor]
            komp_vor_sensor.delete()

    def _update_werte(self):
        db = Datenbank()
        query = 'UPDATE Komponenten SET Anlage=?, Funktion=?, Info=? WHERE Name=?'
        params = ['virtuell', 'signal', '1', self._name]
        db.set_query(query, params)

    def _set_part(self, eigenschaft):
        if eigenschaft.Value:
            self._update_eigenschaft_verbundener_komps(eigenschaft, 'OutInterface')
            self._update_eigenschaft_verbundener_komps(eigenschaft)

        if eigenschaft.Value and self._creator.Part != eigenschaft.Value:
            produkt = self._app.findComponent(eigenschaft.Value)
            uri = produkt.Uri
            self._creator.Part = uri

    def _update_eigenschaft_verbundener_komps(self, eigenschaft, iface_name='InInterface'):
        komp = self._komp
        while True:
            interface = self._komp.findBehaviour(iface_name)
            komp = interface.ConnectedComponent
  
            if komp:
                prop = komp.getProperty(eigenschaft.Name)
                if prop and prop.Value != eigenschaft.Value:
                    prop.Value = eigenschaft.Value
                else:
                    break
            else:
                break

    def _konfiguriere_behaviours(self, vcscript, komp):
        if not self._creator:
            self._creator = komp.createBehaviour(vcscript.VC_COMPONENTCREATOR, '_ComponentCreator')

        if not self._container:
            self._container = komp.createBehaviour(vcscript.VC_COMPONENTCONTAINER, '_ComponentContainer')

    def _konfiguriere_properties(self, vcscript, komp):
        if not self._real_signal:
            self._real_signal = komp.createProperty(vcscript.VC_REAL, '_Signal_real')
            self._real_signal.IsVisible = False
        if not self.produkt:
            self.produkt = komp.createProperty(vcscript.VC_STRING, 'Produkt')

    def _konfiguriere_verbindungen(self):
        container_input = self._container.getConnector('Input')
        if not container_input.Connection:
            creator_output = self._creator.getConnector('Output')
            container_input.connect(creator_output)


        
        
