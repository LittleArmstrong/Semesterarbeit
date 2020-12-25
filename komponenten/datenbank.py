import sqlite3 
import os

class Datenbank():
    def __init__(self, pfad):
        self.pfad = pfad
        self.verbindung =  sqlite3.connect(self.pfad)
        self.cursor = self.verbindung.cursor()

    def query(self, query, params):
        return self.cursor.execute(query, params)
        
    def set_query(self, query, params=None):
        if not params:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)
        self.commit()

    def create_query(self, tabelle, felder_mit_typen):
        query = 'CREATE TABLE IF NOT EXISTS {} ({}' + ', {}' * (len(felder_mit_typen)-1) + ')'
        query = query.format(tabelle, *felder_mit_typen)
        self.set_query(query)

    def replace_query(self, tabelle, params):
        query = 'INSERT OR REPLACE INTO {} VALUES'.format(tabelle) + ' (?' + ', ? ' * (len(params)-1) + ')'
        self.set_query(query, params)

    def delete_query(self, tabelle, spalten = None, werte = None):
        if not spalten:
            query = 'DELETE FROM {}'.format(tabelle)
            self.set_query(query)
        else:
            query = 'DELETE FROM {} WHERE ' + '{} = ?' + 'AND {} = ?' * len(spalten - 1)
            query = query.format(tabelle, *spalten)
            self.set_query(query, werte)
    
    def get_all_data(self, tabelle, sofort = True):
        query = 'SELECT * FROM {}'.format(tabelle)
        self.cursor.execute(query)
        if sofort:
            return self.cursor.fetchall()
        else:
            return self.cursor

    def commit(self):
        self.verbindung.commit()

    def __del__(self):
        self.verbindung.close()

if __name__ == "__main__":
    pass