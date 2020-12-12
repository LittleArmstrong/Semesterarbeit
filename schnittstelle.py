from datenbank import Datenbank
from ast import literal_eval


TYPEN = ['Feeder', 'Transport']

class Schnittstelle():
    def __init__(self, vcscript, anlage):
        app = vcscript.getApplication()
        all_komps = app.Components

        self._delay = vcscript.delay
        self._anlage = anlage
        self._komp = vcscript.getComponent()
        self._all_komps = {komp.Name : komp for komp in all_komps}


    def OnRun(self):
        while True:
            db=Datenbank()
            alle_db_zeilen = db.get_all_data(sofort=False)
            db_zeile = {}
            update_db=[]
            
            for zeile in alle_db_zeilen:
                db_zeile['Name'], db_zeile['Anlage'], db_zeile['Typ'], db_zeile['Funktion'], db_zeile['Info'] = zeile
                if db_zeile['Typ'] == 'Feeder' and db_zeile['Funktion'] != '' and db_zeile['Anlage'] == self._anlage:
                    self._signal_feeder(db_zeile, update_db)

            if update_db:
                self.update_werte(db, update_db)

            if self._anlage == 'real':
                self._delay(0.4)
            else:
                self._delay(0.2)

    def OnStart(self):
        self.reset_werte()

    def OnSignal(self, signal):
        pass
    
    def _signal(self, signal, signal_wert, typ):
        if typ == 'string':
            signal.signal(repr(signal_wert))
        elif typ == 'real':
            signal.signal(signal_wert)

    def _signal_feeder(self, db_zeile, update_db):
        signal_wert = {key:db_zeile[key] for key in ('Funktion', 'Info')}
        komp = self._all_komps[db_zeile['Name']]
        signal = komp.getBehaviour('_StringSignal')
        self._signal(signal, signal_wert, typ='string')

        if self._anlage == 'real':
            update_zeile = ('virtuell', db_zeile['Funktion'], db_zeile['Info'], db_zeile['Name'])
            update_db.append(update_zeile)
        
        elif self._anlage == 'virtuell':
            update_zeile = ('', '', '', db_zeile['Name'])
            update_db.append(update_zeile)
        

    def update_werte(self, db, update):
        query = 'UPDATE Komponenten SET Anlage=?, Funktion = ?, Info = ? WHERE Name=?'
        for params in update:
            db.set_query(query, params)

    def reset_werte(self):
        komps_mit_typen = [(name, komp.getProperty('Typ').Value) for name, komp in self._all_komps.items() if komp.getProperty('Typ')\
             and komp.getProperty('Typ').Value in TYPEN]
        db=Datenbank()
        query='DELETE FROM Komponenten'
        db.set_query(query,'')
        query='INSERT INTO Komponenten VALUES(?,?,?,?,?)'

        for name, typ in komps_mit_typen:
            params = (name, '', typ, '', '')
            db.set_query(query, params)


    
