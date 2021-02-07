#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Creator():
    """Klasse zum Erstellen von Komponenten für die Förderbänder (Transport). Irgendeine Komponente nutzbar. Pythonscript namens Script 
    hinzufügen mit folgendem Inhalt:
    import vcScript
    from vccode import Creator

    Creator(vcScript)
    
    Attribute
    - - - - -
    App - vcApplication
        Referenz zur Anwendung
    Komponente - vcComponent
        diese Komponente
    Produkte - vcProperty
        die zu erstellenden Produkte
    Vcscript - module
        Modul vcScript

    Methode
    - - - - -
    konfig_creator(prod=None) -> None
        erstellt ComponentCreator der gleichen Anzahl an Produkten in der Eigenschaft Produkte
    """
    def __init__(self, vcscript):
        """Legt Attribute fest, erstellt Eigenschaft Produkte und erstellt ComponentCreator, welche bei Änderung der Eigenschaft
        Produkte nochmal geprüft werden.

        Parameter
        - - - - -
        vcscript - module
            Modul vcScript
        """
        # Eigenschaften
        self.App = vcscript.getApplication()
        self.Komponente = vcscript.getComponent()
        self.Komponente.Name = 'Creator'
        self.Produkte = self.Komponente.getProperty('Schnittstelle::Produkte')
        self.Vcscript = vcscript
        # Erstelle Eigenschaft Produkte falls nicht vorhanden
        if not self.Produkte:
            self.Produkte = self.Komponente.createProperty(vcscript.VC_STRING, 'Schnittstelle::Produkte')
        self.Produkte.OnChanged = self.konfig_creator
        # Erstelle ComponentCreator und -Container zum Erstellen und Aufbewahren von Komponenten
        self.konfig_creator()

    def konfig_creator(self, prod=None):
        """Erstelle ComponentCreator abh. von der Anzahl an mit Komma getrennten Produkten in der Eigenschaft Produkte.
        Die ComponentCreator werden nach dem Produktnamen + __HIDE__ genannt.

        Parameter
        - - - - -
        prod=None - vcProperty
            notwendig, da das Event OnChanged einer Eigenschaft sich selbst als Argument der bestimmten Funktion auswählt
        """
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
            try:
                uri = self.App.findComponent(produkt).Uri
            except:
                print(self.Komponente.Name, 'Produkt {} im Layout nicht gefunden.'.format(produkt))
            container = alle_container[i]
            creator.Name = produkt + '__HIDE__'
            container.Name = produkt + '__HIDE__'
            creator.Part = uri
            creator.getConnector('Output').connect(container.getConnector('Input'))
