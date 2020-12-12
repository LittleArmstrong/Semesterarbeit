import tkinter as tk
from tkinter import ttk
from datenbank import Datenbank

TYP = 'Feeder'

class FeederSteuerung:
    def __init__(self, tab_parent, komps_typ_feeder):
        if not komps_typ_feeder:
            komps_typ_feeder = ['None']
        self.main(tab_parent, komps_typ_feeder)

    def main(self, tab_parent, komps_typ_feeder):
        tab_feeder = ttk.Frame(tab_parent)
        tab_parent.add(tab_feeder, text='Feeder')
        
        self.funktion_erstelle(tab_feeder, komps_typ_feeder)
        self.funktion_erstelle_im_intervall(tab_feeder, komps_typ_feeder)
    

    def funktion_erstelle(self, tab_feeder, komps_typ_feeder):
        erstelle_var_feeder_komponente = tk.StringVar()
        erstelle_var_feeder_komponente.set(komps_typ_feeder[0])

        erstelle_auswahl_komponente_typ_feeder = tk.OptionMenu(tab_feeder, erstelle_var_feeder_komponente, *komps_typ_feeder)
        erstelle_auswahl_komponente_typ_feeder.grid(row=0, column=0, padx=10, pady=15, sticky='W')

        erstelle_button = tk.Button(tab_feeder, text='Erstelle', command= lambda: self.cmd_erstelle(erstelle_var_feeder_komponente.get()))
        erstelle_button.grid(row=0, column=1, padx=10, pady=15, sticky='W')

    def cmd_erstelle(self, komp_name):
        db=Datenbank()
        query = 'UPDATE Komponenten SET Anlage = ?, Funktion = ?, Info = ? WHERE Name = ?'
        params = ('real', 'erstelle', '', komp_name)
        db.set_query(query, params)

    def funktion_erstelle_im_intervall(self, tab_feeder, komps_typ_feeder):
        intervall_var_direkt_erstellen = tk.IntVar()
        intervall_var_direkt_erstellen.set(1)
        intervall_var_intervall = tk.StringVar()
        intervall_var_intervall.set('0')
        intervall_var_komponente_typ_feeder = tk.StringVar()
        intervall_var_komponente_typ_feeder.set(komps_typ_feeder[0])

        intervall_auswahl_komponente_typ_feeder = tk.OptionMenu(tab_feeder, intervall_var_komponente_typ_feeder, *komps_typ_feeder)
        intervall_auswahl_komponente_typ_feeder.grid(row=1, column=0, padx=10, pady=0, sticky='W')

        vcmd = (tab_feeder.register(self.OnValidierung), '%P')
        intervall_entry = tk.Entry(tab_feeder, text='0', textvariable=intervall_var_intervall, validate='key', validatecommand=vcmd)
        intervall_entry.grid(row=1, column=1, padx=10, pady=0, sticky='W')

        intervall_checkbox = tk.Checkbutton(tab_feeder, text='Direkt', variable=intervall_var_direkt_erstellen)
        intervall_checkbox.grid(row=1, column=2, padx=10, pady=0, sticky='W')

        intervall_button_cmd = lambda: self.cmd_funktion_erstelle_im_intervall(\
            intervall_var_direkt_erstellen.get(),  intervall_var_komponente_typ_feeder.get(), intervall_var_intervall.get())
        intervall_button = tk.Button(tab_feeder, text='Erstelle', command = intervall_button_cmd)
        intervall_button.grid(row=1, column=3, padx=10, pady=0, sticky='W')

    def OnValidierung(self, entry_wert):
        if entry_wert.isdigit() or entry_wert == '':
            return True
        else:
            return False

    def cmd_funktion_erstelle_im_intervall(self, checkbox_wert, komp_name, intervall):
        if checkbox_wert:
            funktion = 'intervall_direkt'
        else:
            funktion = 'intervall'
        db=Datenbank()
        query='UPDATE Komponenten SET Anlage=?, Funktion=?, Info=? WHERE Name=?'
        params=('real', funktion, intervall or '0', komp_name)
        db.set_query(query, params)

