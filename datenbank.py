import sqlite3 
import os

DB_DATEI = r'Datenbank.db'

class Datenbank():
    def __init__(self):
        self.verbindung =  sqlite3.connect(DB_DATEI)
        self.cursor = self.verbindung.cursor()
        if  os.stat(DB_DATEI).st_size==0:
            query = '''CREATE TABLE IF NOT EXISTS Komponenten (
                        Name String Primary Key Unique, Anlage String, Typ String, Funktion String, Info String)'''
            self.cursor.execute(query)
            self.verbindung.commit()

    def query(self, query, params):
        return self.cursor.execute(query, params)
        
    def set_query(self, query, params):
        self.cursor.execute(query, params)
        self.commit()
    
    def get_all_data(self, sofort = True):
        self.cursor.execute('SELECT * FROM Komponenten')
        if sofort:
            return self.cursor.fetchall()
        else:
            return self.cursor

    def commit(self):
        self.verbindung.commit()

    def __del__(self):
        self.verbindung.close()

if __name__ == "__main__":
    db=Datenbank()
    params=('FB1', 'real', 'Transport', '', '')
    db.query('INSERT INTO Komponenten VALUES(?,?,?,?,?)', params)
    db.commit()
    print(db.query('SELECT * FROM Komponenten', '').fetchall())