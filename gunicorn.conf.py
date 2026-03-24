"""Gunicorn Konfiguration mit optionalem HTTPS-Support"""
import os

# Basis-Konfiguration
bind = "0.0.0.0:5000"
workers = 2
threads = 4
worker_class = "gthread"

# SSL-Konfiguration (optional)
ssl_certfile = "/app/data/server.crt"
ssl_keyfile = "/app/data/server.key"

# Prüfen ob SSL-Zertifikate vorhanden sind
if os.path.exists(ssl_certfile) and os.path.exists(ssl_keyfile):
    certfile = ssl_certfile
    keyfile = ssl_keyfile
    print(f"HTTPS aktiviert mit Zertifikaten aus /app/data/")
else:
    certfile = None
    keyfile = None
    print("Keine SSL-Zertifikate gefunden - HTTP-Modus")

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Timeouts
timeout = 120
graceful_timeout = 30
keepalive = 5
