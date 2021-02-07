# Semesterarbeit - Schnittstelle zwischen realer und virtueller Anlage
# Projektanleitung
## 1 Pfad zum Sqlite-Modul in der Umgebungsvariable speichern
In Visual Components 4.2 muss der Pfad zum sqlite-Modul in der Umgebungsvariable PATH gespeichert werden, damit diese importiert werden kann. Dieser befindet sich im Ordner DLLS, welches (abh. vom Installationsort) folgenden Pfad hat: „C:\Program Files\Visual Components\Visual Components Premium 4.2\Python\DLLs“.

Pfad der Umgebungsvariable hinzufügen (Win10):
1. Im Suchfeld der Taskleiste (Start) „Umgebungsvariable“ suchen und auf „Umgebungsvariablen für dieses Konto bearbeiten“ klicken.
1. Auf „Umgebungsvariablen“ klicken.
1. Oben in der Liste „Path“ wählen und auf „Bearbeiten“ klicken.
1. Auf „Neu“ klicken, den Pfad hinzufügen und auf „OK“ klicken

## 2 Download des Projekts von GitHub
Der Projektordner sollte entweder über git (git pull) oder über „Code>Download Zip“ runtergeladen und ggf. extrahiert werden.

## 3 Pfade festlegen
Der Pfad zum Projektordner (z.B. r'C:\Users\Baris\Desktop\Semesterarbeit') sollte in den Dateien *vccode.py* und *konst.py* der jeweiligen Variable zugewiesen werden.

*vccode.py*: pfad_zum_code = *r'C:\Users\Baris\Desktop\Semesterarbeit'*  
*konst.py*: PFAD = *'C:\\Users\\Baris\\Desktop\\Semesterarbeit\\datenbanken\\'* (Schrägstriche doppelt)  

Bei *konst.py* ist es nicht möglich die r-Notation (s.o.) zu Nutzen, da am Ende des Strings auch ein Schrägstrich vorkommt.

## 4 Komponente zum Importieren bereitstellen
Damit die Code-Dateien auch von Visual Components genutzt werden können, müssen diese im Ordner *site-packages* (*„C:\Program Files\Visual Components\Visual Components Premium 4.2\Python\lib\site-packages“*) gespeichert werden.

Da die Klassen schon vom Modul *vccode.py* importiert werden, muss nur diese Datei im Ordner *site-packages* gespeichert werden.

## 5 Projekt starten
Zum Starten des Projekts müssen folgende Dateien geöffnet werden: *real.vcmx*, *virtuell.vcmx* und *steuerung.pyw*. Die Fenster von *real.vcmx* und *virtuell.vcmx* sollten nebeneinander gelegt werden, damit diese miteinander verglichen werden können.

Über *steuerung.pyw* können Befehle an die reale Anlage gesendet werden. Die virtuelle Anlage sollte sich der realen Anlage anpassen. Dies kann man sehen, wenn man eine der Anlagen für kurze Zeit pausiert und dann wieder startet.



