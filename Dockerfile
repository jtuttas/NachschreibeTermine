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

# Port freigeben
EXPOSE 5000

# Umgebungsvariablen
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Gunicorn als Production-Server
RUN pip install --no-cache-dir gunicorn

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

# Anwendung starten
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "app:app"]
