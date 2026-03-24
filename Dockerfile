# Python 3.11 Slim Image
FROM python:3.11-slim

# Arbeitsverzeichnis
WORKDIR /app

# System-Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python-Dependencies installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Nicht-Root-Benutzer erstellen
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Port freigeben (5000 für HTTP/HTTPS)
EXPOSE 5000

# Umgebungsvariablen
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Gunicorn als Production-Server
RUN pip install --no-cache-dir gunicorn

# Gunicorn Konfiguration kopieren
COPY gunicorn.conf.py .

# Healthcheck (ohne SSL-Validierung für selbstsignierte Zertifikate)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; import ssl; ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE; urllib.request.urlopen('https://localhost:5000/', context=ctx)" || exit 1

# Anwendung starten mit Konfigurationsdatei
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
