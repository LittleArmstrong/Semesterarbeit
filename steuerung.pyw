import tkinter as tk
from tkinter import ttk
from komponenten.datenbank import Datenbank
from steuerung_gui.feeder_tab import FeederTab
from steuerung_gui.transport_tab import TransportTab
import konstanten

# --- Fenster
fenster = tk.Tk()
fenster.title('Steuerung')
fenster.geometry('500x280')

tab_parent = ttk.Notebook()

# --- Wahllisten
pfad = konstanten.PFAD_KOMPONENTEN
tabelle = konstanten.TABELLE_KOMPONENTEN
db = Datenbank(pfad)
cursor = db.get_all_data(tabelle, sofort = False)
alle_komponenten_mit_typ = [(name, typ) for name, typ in cursor]
komponenten_mit_typ_feeder = [name for name, typ in alle_komponenten_mit_typ if typ == 'Feeder']
komponenten_mit_typ_transport = [name for name, typ in alle_komponenten_mit_typ if typ == 'Transport']

# --- Feeder-Tab
FeederTab(tab_parent, komponenten_mit_typ_feeder)

# --- Transport-Tab
TransportTab(tab_parent, komponenten_mit_typ_transport)

tab_parent.pack(expand=1, fill='both')
fenster.mainloop()
