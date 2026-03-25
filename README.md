# Nachschreibetermine Buchungssystem

[![Docker Build](https://github.com/jtuttas/NachschreibeTermine/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/jtuttas/NachschreibeTermine/actions/workflows/docker-publish.yml)

Ein Flask-basiertes Buchungssystem für Nachschreibetermine an Schulen.

## Features

- **Microsoft Azure AD Authentifizierung** - Sichere Anmeldung für Lehrkräfte
- **Terminverwaltung** - Automatisches Einlesen von Terminen aus CSV
- **Schülerbuchung** - Einfaches Eintragen von Schülern für Nachschreibetermine
- **Teilnehmerlisten** - Übersicht und PDF-Export
- **Anwesenheitskontrolle** - Bestätigung der Anwesenheit während des Termins
- **E-Mail-Berichte** - Automatische Tagesberichte um 23:59

## Installation

### Voraussetzungen

- Python 3.10+
- pip

### Setup

1. **Repository klonen und in das Verzeichnis wechseln:**
   ```bash
   cd NachschreibeTermine
   ```

2. **Virtuelle Umgebung erstellen und aktivieren:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Umgebungsvariablen konfigurieren:**
   ```bash
   # .env.example nach .env kopieren und anpassen
   cp .env.example .env
   ```

5. **Azure AD App Registration erstellen** (für Produktion):
   
   **Grundkonfiguration:**
   - Gehe zu Azure Portal > Microsoft Entra ID > App registrations
   - Neue Registrierung erstellen
   - Redirect URI hinzufügen (Platform: **Web**):
     - Entwicklung: `http://localhost:5000/auth/callback`
     - Produktion: `https://deine-domain.de:5001/auth/callback`
   - Client Secret erstellen
   - Werte in `.env` eintragen

   **API-Berechtigungen konfigurieren:**
   - API permissions > Add a permission > Microsoft Graph > Delegated permissions
   - Folgende Berechtigungen hinzufügen:
     - `User.Read` (Anmelden und Profil lesen)
     - `GroupMember.Read.All` (Gruppenmitgliedschaften lesen)
   - **"Administratorzustimmung erteilen"** klicken

   **Gruppenbasierter Zugriff (optional):**
   - Nur Mitglieder einer bestimmten Azure AD Gruppe können sich anmelden
   - Gruppen-ID finden: Azure Portal > Groups > Deine Gruppe > Object ID
   - Umgebungsvariable setzen: `AZURE_ALLOWED_GROUP=Lehrer` (Name oder ID)

6. **Termine konfigurieren:**
   
   **Option A: OneDrive/SharePoint (empfohlen)**
   1. CSV-Datei in OneDrive/SharePoint hochladen
   2. Rechtsklick auf Datei → "Freigeben" → "Link kopieren" → "Jeder mit dem Link"
   3. Link als `TERMINE_CSV_URL` in `.env` setzen
   4. Für direkten Download-Link `&download=1` anhängen
   
   ```env
   TERMINE_CSV_URL=https://your-tenant.sharepoint.com/:x:/s/site/abc123?download=1
   ```
   
   **Option B: Lokale Datei (Fallback)**
   Datei `termine.csv` mit folgendem Format:
   ```csv
   datum,uhrzeit,aufsicht_email,raum
   2026-03-25,08:00,mueller@schule.de,A101
   ```

7. **Anwendung starten:**
   ```bash
   python app.py
   ```

8. **Browser öffnen:** http://localhost:5000

## Docker

### Mit Docker Compose (empfohlen)

```bash
# Container bauen und starten
docker compose up -d

# Logs anzeigen
docker compose logs -f

# Container stoppen
docker compose down
```

### Image aus GitHub Container Registry

```bash
docker pull ghcr.io/jtuttas/nachschreibetermine:latest

# Container starten (minimal)
docker run -d -p 5000:5000 \
  -e SECRET_KEY=your-secret-key \
  -e DEBUG_MODE=True \
  -e DATABASE_URL=sqlite:////app/data/nachschreibetermine.db \
  -v ./data:/app/data \
  -v ./termine.csv:/app/data/termine.csv:ro \
  ghcr.io/jtuttas/nachschreibetermine:latest

# Container mit Azure AD Authentifizierung starten
docker run -d -p 5001:5000 \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=sqlite:////app/data/nachschreibetermine.db \
  -e AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx \
  -e AZURE_CLIENT_SECRET=your-client-secret \
  -e AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx \
  -e AZURE_ALLOWED_GROUP=Lehrer \
  -v ./data:/app/data \
  -v ./termine.csv:/app/data/termine.csv:ro \
  ghcr.io/jtuttas/nachschreibetermine:latest
```

### Manuell mit Docker

```bash
# Image bauen
docker build -t nachschreibetermine .

# Container starten
docker run -d -p 5000:5000 \
  -e SECRET_KEY=your-secret-key \
  -e DEBUG_MODE=True \
  -e DATABASE_URL=sqlite:////app/data/nachschreibetermine.db \
  -v ./data:/app/data \
  -v ./termine.csv:/app/data/termine.csv:ro \
  nachschreibetermine
```

### Persistente Daten

Die SQLite-Datenbank wird im `data/`-Verzeichnis gespeichert und bleibt bei Container-Neustarts erhalten.

**Wichtig:** Die Umgebungsvariable `DATABASE_URL=sqlite:////app/data/nachschreibetermine.db` (beachte die 4 Schrägstriche für den absoluten Pfad) muss gesetzt werden, damit die Datenbank im gemounteten Volume gespeichert wird. Ohne diese Variable wird die Datenbank im Container-internen Verzeichnis erstellt und geht bei Neustarts verloren.

### HTTPS-Konfiguration

Für HTTPS-Support platziere die Zertifikate im `data/`-Verzeichnis:

```bash
data/
├── server.crt    # SSL-Zertifikat
└── server.key    # Privater Schlüssel
```

Die Anwendung erkennt automatisch die Zertifikate und aktiviert HTTPS. Der Container lauscht dann auf Port 443:

```bash
# Container mit HTTPS starten
docker compose up -d

# Zugriff über HTTPS
https://localhost
```

Ohne Zertifikate läuft die Anwendung im HTTP-Modus.

## Debug-Login

Im Entwicklungsmodus (`DEBUG_MODE=True`) kann der Testbenutzer verwendet werden:

- **Benutzername:** `user`
- **Passwort:** `user`

## Konfiguration

### Umgebungsvariablen (.env)

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `SECRET_KEY` | Flask Secret Key | dev-secret-key |
| `DATABASE_URL` | Datenbank-Pfad | sqlite:///nachschreibetermine.db |
| `MAX_SCHUELER_PRO_TERMIN` | Max. Schüler pro Termin | 30 |
| `DEBUG_MODE` | Debug-Login aktivieren | False |
| `TERMINE_CSV_URL` | OneDrive/SharePoint Download-Link für Termine (Priorität) | - |
| `TERMINE_CSV_PATH` | Lokaler Fallback-Pfad zur Termin-CSV | termine.csv |

**Azure AD Authentifizierung:**

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `AZURE_CLIENT_ID` | Azure AD Application (Client) ID | - |
| `AZURE_CLIENT_SECRET` | Azure AD Client Secret | - |
| `AZURE_TENANT_ID` | Azure AD Directory (Tenant) ID | - |
| `AZURE_ALLOWED_GROUP` | Gruppenname oder Object-ID zur Zugriffsbeschränkung | Lehrer |

> **Hinweis für Docker:** Setze `DATABASE_URL=sqlite:////app/data/nachschreibetermine.db` (4 Schrägstriche für absoluten Pfad) um die Datenbank im gemounteten Volume zu persistieren.

### E-Mail Konfiguration

Für automatische Tagesberichte:
- `MAIL_SERVER` - SMTP Server
- `MAIL_PORT` - SMTP Port (Standard: 587)
- `MAIL_USERNAME` - E-Mail Benutzername
- `MAIL_PASSWORD` - E-Mail Passwort

## Projektstruktur

```
NachschreibeTermine/
├── app.py              # Hauptanwendung
├── config.py           # Konfiguration
├── models.py           # Datenbankmodelle
├── routes.py           # URL-Routen
├── auth.py             # Authentifizierung
├── email_service.py    # E-Mail & Scheduler
├── requirements.txt    # Python-Abhängigkeiten
├── termine.csv         # Termin-Daten
├── .env               # Umgebungsvariablen
├── templates/         # HTML-Templates
│   ├── base.html
│   ├── dashboard.html
│   ├── unauthorized.html
│   ├── auth/
│   │   └── login.html
│   └── termine/
│       ├── detail.html
│       ├── buchen.html
│       └── teilnehmerliste.html
└── static/
    └── css/
        └── style.css
```

## Lizenz

MIT License
