"""Gunicorn Konfiguration mit optionalem HTTPS-Support"""
import os

# Basis-Konfiguration
bind = "0.0.0.0:5000"
workers = 2
threads = 4
worker_class = "gthread"
preload_app = True

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


def post_fork(server, worker):
    """Dispose SQLAlchemy connection pool after fork so each worker gets fresh connections."""
    try:
        from app import app
        from models import db
        with app.app_context():
            db.engine.dispose()
    except Exception as e:
        server.log.warning(f'post_fork: could not dispose DB connections: {e}')


# Timeouts
timeout = 120
graceful_timeout = 30
keepalive = 5
