#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3 
import os

class Datenbank():
    """ Klasse zum Interagieren mit den Datenbanken.

    Attribute
    - - - - -
    Verbindung - Connection
        Verbindung zur Datenbank
    Cursor - Cursor
        Cursor-Objekt zum Ausführen von SQL-Befehlen
    
    Methoden
    - - - - -
    commit() -> None
        speichert die Daten in der Datenbank
    create_query(tabelle, felder) -> None
        Erstellt eine Tabelle
    delete_query(tabelle, spalten=None, werte=None) -> None
        Lösch bestimmte Einträge in Datenbank oder alles
    get_all_data(tabelle, sofort=None) -> cursor or list
        erhalte alle Einträge in der Datenbank als cursor (iterator) oder liste
    insert_query(tabelle, params) -> None
        füge ein Eintrag der Datenbank hinzu
    query(query, params) -> list or cursor
        führe SQL-Befehl aus und gib Ergebnis zurück
    replace_query(tabelle, params) -> None 
        fügt ein Eintrag der Datenbank hinzu und ersetzt die Zeile bei gleichem Wert in primary key Spalte
    set_query(query, params=None) -> None
        führt SQL-Befehl aus und speichert (committed) diesen
    """
    def __init__(self, pfad):
        """
        Parameter
        - - - - -
        pfad - str
            Pfad zur Datenbank
        """
        self.Verbindung =  sqlite3.connect(pfad)
        self.Cursor = self.Verbindung.cursor()
    
    def __del__(self):
        """Schließe die Verbindung zur Datenbank, wenn das Objekt gelöscht wird.
        """
        self.Verbindung.close()
    
    def commit(self):
        """Speicher alle Änderungen.
        """
        self.Verbindung.commit()
    
    def create_query(self, tabelle, felder):
        """Erstelle Tabelle mit gewünschtem Namen und Spalten.
        Parameter
        - - - - -
        tabelle - str
            Name der Tabelle
        felder - list of str
            Spalten und deren Typ, z.B. ['Name String', 'ID Integer']
        """
        query = 'CREATE TABLE IF NOT EXISTS {} ({}' + ', {}' * (len(felder)-1) + ')'
        query = query.format(tabelle, *felder)
        self.set_query(query)
    
    def delete_query(self, tabelle, spalten = None, werte = None):
        """Löscht normal alle Einträge in der Tabelle. Spezifische Einträge werden durch das Suchkriterium WHERE spalte1=feld1 
        und spalte2=feld2 gelöscht.

        Parameter
        - - - - -
        tabelle - str
            Name der Tabelle
        spalten=None - str, optional
            Suchkriteriumsspalten z.B. ['Name', 'ID']
        werte=None - str, optional
            Suchkriteriumswerte z.B. ['Ali', 2]
        """
        if not spalten:
            query = 'DELETE FROM {}'.format(tabelle)
            self.set_query(query)
        else:
            query = 'DELETE FROM {} WHERE ' + '{} = ?' + 'AND {} = ?' * len(spalten - 1)
            query = query.format(tabelle, *spalten)
            self.set_query(query, werte)
    
    def get_all_data(self, tabelle, sofort = True):
        """Erhalte alle Einträge in der Tabelle entweder direkt als Liste oder als einzeln iterierend mit Cursor-Objekt.

        Parameter
        - - - - -
        tabelle - str
            Name der Tabelle
        sofort=True - bool, optional
            True: alle Einträge als Liste zurück, False: Cursor-Objekt zurück

        Rückgabe
        - - - - -
        list or cursor
        """
        query = 'SELECT * FROM {}'.format(tabelle)
        self.Cursor.execute(query)
        if sofort:
            return self.Cursor.fetchall()
        else:
            return self.Cursor
    
    def insert_query(self, tabelle, params):
        """Erstellt einen neuen Eintrag.

        Parameter
        - - - - - 
        tabelle - str
            Name der Tabelle
        params - list
            Werte für die Spalten
        """
        query = 'INSERT INTO {} VALUES'.format(tabelle) + ' (?' + ', ? ' * (len(params)-1) + ')'
        self.set_query(query, params)

    def query(self, query, params, sofort=False):
        """Führt SQL-Befehl aus und gibt Ergebnis zurück. Wird nicht gespeichert, dafür ist commit() notwendig.

        Parameter
        - - - - - 
        query - str
            der auszuführende SQL-Befehl
        params - list
            die Werte

        Rückgabe
        - - - - -
        list or cursor
        """
        self.Cursor.execute(query, params)
        if sofort:
            return self.Cursor.fetchall()
        else:
            return self.Cursor
    
    def replace_query(self, tabelle, params):
        """Erstellt einen neuen Eintrag und überschreibt den alten, wenn die Primary Keys gleich sind.

        Parameter
        - - - - - 
        tabelle - str
            Name der Tabelle
        params - list
            Werte für die Spalten
        """
        query = 'INSERT OR REPLACE INTO {} VALUES'.format(tabelle) + ' (?' + ', ? ' * (len(params)-1) + ')'
        self.set_query(query, params)
        
    def set_query(self, query, params=None):
        """Wie query(query, params), nur dass direkt danach auch gespeichert wird

        Parameter
        - - - - - 
        query - str
            der auszuführende SQL-Befehl
        params=None, optional
            die Werte für den Befehl
        """
        if not params:
            self.Cursor.execute(query)
        else:
            self.Cursor.execute(query, params)
        self.commit()

    

    
