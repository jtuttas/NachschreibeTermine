# Nachschreibe Termine Buchungssystem

## Zweck der Anwendung

Die Anwendung soll es ermöglichen Lehrkräften Termine zur Nachschreibung von Klassenarbeit zu Erstellen.

## Sicherheitsanforderungen

Alle Parameter und Credentials sollen in einer .env Datei gespeichert werden, damit sie nicht im Code sichtbar sind.

## Funktionale Anforderungen

### Buchung von Nachschreibeterminen

Lehrkräfte können sich am System anmelden. Die Authentifizierung soll über Microsoft Azure Entra ID
erfolgen. Nur Benutzer die auch in der Gruppe "Lehrer" sind sollten Zugriff auf die Anwendung haben.

Für Debugging Zwecke soll es eine Testbenutzer geben, der Zugriff auf die Anwendung hat. Dieses Authentifiziert mit mit dem benutzernamen "user" und dem Kennwort "user". Dieser Benutzer soll nicht in der Gruppe "Lehrer" sein, damit er nur Zugriff auf die Debugging Funktionen hat.

Die Termine für die Nachschreibetermin sind fest gelegt. Eine CSV Datei enthält den Termin und die Email Adresse des Aufsichtsführenden Lehrkraft. Die Termine sollen automatisch aus der CSV Datei eingelesen und in der Anwendung angezeigt werden.

Nach der Anmeldung sieht ein Lehre ein hübsches Dashboard und hat die Möglichkeit Nachschreiber an Terminen für die Nachschreibung zu buchen. Termine die in der Vergangenheit liegen werden nicht angezeigt.

Die Lehrkraft hat nun die Möglichkeit einen Termin zu wählen und dort Schüler eintragen die an diesem Termin teilnehmen sollen. Es soll möglich sein mehrere Schüler für einen Termin einzutragen. Maximal sollen 30 Termine pro Tag möglich sein (dieses ist ein Default wert, der über einen Parameter anzupassen ist). Es soll nicht möglich sein einen Termin zu wählen, der bereits 30 Schüler hat.

Fügt die Lehrkraft einen neuen Schüler hinzu so sind folgende Informationen notwendig:

- Name des Schülers
- Dauer der Klassenarbeit
- Ob es sich um eine Papierklassenarbeit handelt oder um eine digitale Klassenarbeit (als Checkbox)
- Wenn es sich um eine Moodle Klassenarbeit handelt, soll die URL zum Moodle Kurs eingegeben werden können und das Passwort für die Klassenarbeit.

### Durchführung der Nachschreibung

Am Tag der Nachschreibung soll die Lehrkraft die Möglichkeit haben die Teilnehmerliste für den Termin zu sehen. Schüler die anwesend sind kann er durch ein Häkchen markieren. Es soll möglich sein die Teilnehmerliste als PDF zu exportieren, damit sie ausgedruckt werden kann.

Am Ende ende eines Nachschreibetermin um 23:59 soll den Lehrkräften die einen Schüler zur eine Liste der Schüler geschickt bekommen, die an diesem Termin teilgenommen haben. Diese Liste soll die Informationen über die Schüler enthalten, die von der Lehrkraft eingetragen wurden.Auch fehlende Schüler sollen in der Liste markiert werden, damit die Lehrkraft weiß welche Schüler nicht anwesend waren.

## Nicht Funktionale Anforderungen

Die Anwendung sollte sowohl auf Desktop als auch auf mobilen Geräten nutzbar sein. Sie soll eine benutzerfreundliche Oberfläche haben, die es Lehrkräften ermöglicht schnell und einfach Termine zu buchen und Teilnehmer hinzuzufügen.

## Datenhaltung

Die Daten über die Termine und Teilnehmer sollen in einer SQLITE Datenbank gespeichert werden. Es soll eine Möglichkeit geben die Daten regelmäßig zu sichern, um Datenverlust zu vermeiden.

## Wartbarkeit

Der Code soll gut strukturiert und dokumentiert sein, um die Wartbarkeit zu gewährleisten. Es soll eine klare Trennung zwischen der Logik der Anwendung und der Benutzeroberfläche geben, um die Wartung und Erweiterung der Anwendung zu erleichtern.

## Erweiterbarkeit

Die Anwendung soll so entwickelt werden, dass sie leicht erweitert werden kann, um zukünftige Anforderungen zu erfüllen. Zum Beispiel könnte in Zukunft die Möglichkeit hinzugefügt werden, dass Schüler sich selbst für Nachschreibtermine anmelden können, oder dass Lehrkräfte die Möglichkeit haben, Termine zu stornieren oder zu verschieben.

