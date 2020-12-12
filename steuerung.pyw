import tkinter as tk
from tkinter import ttk
from feeder_steuerung import FeederSteuerung
from datenbank import Datenbank

# --- Fenster
fenster = tk.Tk()
fenster.title('Steuerung')
fenster.geometry('500x280')

tab_parent = ttk.Notebook()

# --- Wahllisten
db = Datenbank()
query='SELECT Name, Typ FROM Komponenten'
params = ''
cursor = db.query(query, params)
komps_typ_feeder = [name for name, typ in cursor if typ=='Feeder']

# --- Feeder-Tab
FeederSteuerung(tab_parent, komps_typ_feeder)

# --- Transport-Tab
tab_transport = ttk.Frame(tab_parent)
tab_parent.add(tab_transport, text='Transport')

tab_parent.pack(expand=1, fill='both')
fenster.mainloop()
