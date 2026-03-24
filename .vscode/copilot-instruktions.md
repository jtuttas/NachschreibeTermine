# Pflichtenheft für die Entwicklung einer Webanwendung

## Architektur & Code-Qualität

### Trennung von Schichten / Clean Architecture

- UI, Business-Logik und Datenzugriff klar trennen (z.B. Services, Repositories).

- Keine direkten DB-/API-Aufrufe aus React-Components, sondern über abstrahierte Services.

### Code-Qualität

- **Linting**: Verwenden Sie ESLint mit einem Standard-Setup (z.B. Airbnb, StandardJS) für konsistenten Code-Stil.

- **Formatierung**: Nutzen Sie Prettier für automatische Code-Formatierung.

- **TypeScript**: Verwenden Sie TypeScript für statische Typisierung und bessere Wartbarkeit.

### Logging & Fehlerbehandlung

- Implementieren Sie ein zentrales Logging-System (z.B. Winston, Log4js) für Backend-Fehler und wichtige Ereignisse.

## Frontend

Das Frontend der hübsche und moderne Webanwendung wird mit React entwickelt, um eine interaktive und benutzerfreundliche Oberfläche zu gewährleisten. Nutze TypeScript für eine bessere Typensicherheit und Wartbarkeit des Codes.Verwende CSS-Module für die Gestaltung der Benutzeroberfläche.Wie z.B. Tailwind CSS können verwendet werden, um die Entwicklung zu beschleunigen und ein konsistentes Design zu gewährleisten.

Das layout und Design der Anwendung sollte modern und intuitiv sein, um eine einfache Navigation zu ermöglichen.

### UI/UX Anforderungen

- **Logo**: Verwende auf allen Seiten das Logo der Multi Media Berufsbildende Schulen. Siehe Datei ./logo.png. Das Logo sollte auf weißem Hintergrund dargestellt werden.

- *Farbschema*: Verwenden Sie ein ansprechendes Farbschema, das die Lesbarkeit fördert und visuell ansprechend ist. Die Hauptfarbe in RGB ist (20, 80, 140). Die zweite Farbe in RGB ist (30, 135, 200). Die Akzentfarbe in RGB ist (250, 229, 97).

- *Schriftarten*: Verwenden Sie gut lesbare Schriftarten für alle Textelemente. 

- *Layout*: Das Layout sollte responsiv sein und sich an verschiedene Bildschirmgrößen anpassen.

- **Navigation*: Eine klare und einfache Navigation sollte vorhanden sein, um den Benutzern das Auffinden von Funktionen zu erleichtern.

- *Formulare*: Formulare zur Eingabe von Abwesenheitsdaten sollten benutzerfreundlich gestaltet sein, mit klaren Beschriftungen und Validierungsregeln. Die Auswahl zwischen eintägiger und mehrtägiger Abwesenheit sollte deutlich erkennbar sein und als Tabs dargestellt werden, die bei der Auswahl den entsprechenden Eingabebereich anzeigen.


### Qualitätsanforderungen

- **Responsives Design**: Die Anwendung soll auf verschiedenen Geräten (Desktop, Tablet, Smartphone) optimal dargestellt werden.

- **Barrierefreiheit**: Die Anwendung soll den WCAG 2.1 AA-Standards entsprechen, um für alle Benutzer zugänglich zu sein.

- **Performance**: Die Ladezeiten der Seiten sollen unter 2 Sekunden liegen, um eine gute Benutzererfahrung zu gewährleisten.

- **Usability**: Die Benutzeroberfläche soll intuitiv und einfach zu bedienen sein, um die Akzeptanz bei den Benutzern zu erhöhen.

- **Sicherheit**: Schutz vor XSS-Angriffen und anderen Sicherheitslücken.

- **Fehlerbehandlung**: Klare und hilfreiche Fehlermeldungen sollen angezeigt werden, wenn Eingaben ungültig sind oder ein Fehler auftritt.

### Validierungsregeln im Frontend

- **Mehrtätigte Abwesenheiten**: Wenn eine Abwesenheit über mehrere Tage gemeldet wird, müssen sowohl das "Von"- als auch das "Bis"-Datum ausgefüllt werden.

- **Einzeltägige Abwesenheiten**: Bei der Meldung einer Abwesenheit für einen einzelnen Tag muss nur das "Von"-Datum ausgefüllt werden, sowie die "Von"- und "Bis"-Stundeneingaben erfolgen.

- **Von - Datumseingabe**: Das Datum sollte vorausgefüllt sein und das aktuelle Datum anzeigen. Es sollte nicht möglich sein, ein Datum in der Vergangenheit auszuwählen.

- **Bis - Datumseingabe**: Das Datum sollte vorausgefüllt sein und das aktuelle Datum anzeigen. Es sollte nicht möglich sein, ein Datum in der Vergangenheit auszuwählen. Zudem muss das "Bis"-Datum gleich oder nach dem "Von"-Datum liegen. Wird ein "Von"-Datum ausgewählt, das nach dem aktuellen "Bis"-Datum liegt, so soll das "Bis"-Datum automatisch auf das gleiche Datum wie das "Von"-Datum gesetzt werden.

- **Von - Stundeneingabe**: Die Eingabe sollte zwischen 1 und 16 liegen. Eine größere Zahl als die "Bis"-Stundeneingabe ist nicht zulässig.

- **Bis - Stundeneingabe**: Die Eingabe sollte zwischen 1 und 16 liegen. Eine kleiner Zahl als die "Von"-Stundeneingabe ist nicht zulässig.

- **Teamleiter Auswahl**: Es muss wenigstens ein Teamleiter ausgewählt werden, bevor das Formular abgeschickt werden kann.

- **Inline-Validierung** mit verständlichen Texten (kein „Error 400“, sondern: „Bis-Stunde muss größer oder gleich Von-Stunde sein“ etc.).

## Backend

Das Backend der Webanwendung wird mit Node.js oder TypeScript und Express entwickelt, um eine robuste und skalierbare Serverumgebung zu schaffen.

### Sicherheitsanforderungen

- **CORS Richtlinien**: Implementieren Sie CORS-Richtlinien, um den Zugriff auf die API nur von autorisierten Domains zu ermöglichen. Die autorisierten Domains werden in der **.env** Datei konfiguriert.

- **Datenvalidierung**: Validieren Sie alle eingehenden Daten, um sicherzustellen, dass sie den erwarteten Formaten und Typen entsprechen.

- Vorgabe, dass die App nur über HTTPS erreichbar ist.

- **Rate Limiting**: Implementieren Sie Rate Limiting, um Missbrauch der API zu verhindern.

## Deployment

Das backend der Webanwendung wird in Form eines Docker-Containers bereitgestellt, um eine konsistente und portable Umgebung zu gewährleisten.

Die Bereitstellung erfolgt über eine github Action, die den Docker-Container automatisch bei jedem Push in das Haupt-Repository aktualisiert und veröffentlicht.

Zusätzlich soll das Frontend über eine github Action automatisch auf GitHub Pages bereitgestellt werden. 

## Dokumentation

Die Dokumentation der Webanwendung umfasst sowohl technische als auch benutzerorientierte Informationen.

- **Technische Dokumentation**: Beschreibt die Architektur, den Code-Stil, die API-Endpunkte und andere technische Details für Entwickler.

- **Benutzerhandbuch**: Bietet Anleitungen und Hilfestellungen für Endbenutzer zur Nutzung der Anwendung.

- **Wartungsanleitungen**: Enthält Informationen zur Wartung und Aktualisierung der Anwendung für Administratoren.

- **README Datei**: Eine ausführliche README.md Datei im Repository, die eine Übersicht über das Projekt, Installationsanweisungen, Konfigurationsdetails und Anweisungen zur Nutzung der Anwendung enthält.

- **CHANGELOG Datei**: Eine CHANGELOG.md Datei im Repository, die alle Änderungen, Verbesserungen und Fehlerbehebungen in den verschiedenen Versionen der Anwendung dokumentiert.

- **Screenshots**: Visuelle Darstellungen der Benutzeroberfläche und wichtiger Funktionen der Anwendung, um die Dokumentation zu ergänzen.

Die Dokumentation wird in Markdown-Dateien im Repository gepflegt und regelmäßig aktualisiert, um sicherzustellen, dass sie stets aktuell und relevant ist.


