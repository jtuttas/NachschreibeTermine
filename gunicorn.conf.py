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
        from email_service import setup_scheduler

        with app.app_context():
            db.engine.dispose()

        scheduler = setup_scheduler(app)
        if scheduler:
            server.log.info(f'Scheduler in Worker gestartet (pid={worker.pid}).')
        else:
            server.log.info(f'Scheduler-Start in Worker übersprungen (pid={worker.pid}).')
    except Exception as e:
        server.log.warning(f'post_fork: could not dispose DB connections: {e}')


def worker_exit(server, worker):
    """Beendet Hintergrunddienste sauber beim Stoppen eines Workers."""
    try:
        from email_service import shutdown_scheduler

        shutdown_scheduler()
    except Exception as e:
        server.log.warning(f'worker_exit: could not stop scheduler: {e}')


# Timeouts
timeout = 120
graceful_timeout = 30
keepalive = 5
