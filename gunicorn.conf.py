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


def when_ready(server):
    """Startet den APScheduler genau einmal im Gunicorn-Masterprozess."""
    try:
        from app import app
        from email_service import setup_scheduler

        setup_scheduler(app)
        server.log.info('Tagesberichts-Scheduler im Gunicorn-Masterprozess gestartet.')
    except Exception as e:
        server.log.error(f'when_ready: could not start scheduler: {e}')


def on_exit(server):
    """Beendet Hintergrunddienste sauber beim Stoppen von Gunicorn."""
    try:
        from email_service import shutdown_scheduler

        shutdown_scheduler()
    except Exception as e:
        server.log.warning(f'on_exit: could not stop scheduler: {e}')


# Timeouts
timeout = 120
graceful_timeout = 30
keepalive = 5
