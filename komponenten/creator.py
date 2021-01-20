#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Creator():
    # __init__ und exklusive Funktionen
    def __init__(self, vcscript):
        # Referenz zur Anwendung, Komponente und Modul
        self.App = vcscript.getApplication()
        self.Komponente = vcscript.getComponent()
        self.Komponente.Name = 'Creator'
        self.Vcscript = vcscript
        # Eigenschaften
        self.Produkte = self.Komponente.getProperty('Schnittstelle::Produkte')
        if not self.Produkte:
            self.Produkte = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Produkte')
        self.Produkte.OnChanged = self.konfiguriere_creator
        # Erstelle ComponentCreator und -Container zum Erstellen und Aufbewahren von Komponenten
        self.konfiguriere_creator()
    
    def OnStart(self):
        pass

    def OnSignal(self, signal):
        pass

    def OnRun(self):
        pass

    def konfiguriere_creator(self, prod=None):
        produkte = self.Produkte.Value
        alle_creator = None
        # Erstelle abh. von Produktanzahl ComponentCreator
        if produkte:
            produkte = [prod.strip() for prod in produkte.split(',')]
            alle_creator = self.Komponente.findBehavioursByType(self.Vcscript.VC_COMPONENTCREATOR)
            alle_container = self.Komponente.findBehavioursByType(self.Vcscript.VC_COMPONENTCONTAINER)
            diff_creator = len(produkte)- len(alle_creator)
            diff_container = len(produkte)- len(alle_container)
            if diff_creator > 0:
                for i in range(diff_creator):
                    creator = self.Komponente.createBehaviour(self.Vcscript.VC_COMPONENTCREATOR, str(i)+'__HIDE__')
                    creator.Limit = 0
                    creator.Interval = 0
                alle_creator = self.Komponente.findBehavioursByType(self.Vcscript.VC_COMPONENTCREATOR)
            if diff_container > 0:
                for i in range(diff_container):
                    creator = self.Komponente.createBehaviour(self.Vcscript.VC_COMPONENTCONTAINER, str(i)+'__HIDE__')
                alle_container = self.Komponente.findBehavioursByType(self.Vcscript.VC_COMPONENTCONTAINER)
        # Benenne die ComponentCreator nach dem zu erstellenden Produkt
        for i, produkt in enumerate(produkte):
            creator = alle_creator[i]
            container = alle_container[i]
            creator.Name = produkt + '__HIDE__'
            container.Name = produkt + '__HIDE__'
            uri = self.App.findComponent(produkt).Uri
            creator.Part = uri
            creator.getConnector('Output').connect(container.getConnector('Input'))
