import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from config import config
from models import db, init_db
from auth import login_manager
from email_service import mail, setup_scheduler
from routes import auth_bp, main_bp, termine_bp, load_termine_from_csv, cleanup_duplicate_termine

csrf = CSRFProtect()


def create_app(config_name=None):
    """Application Factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # ProxyFix für korrekte URL-Generierung hinter Reverse Proxy (HTTPS)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Extensions initialisieren
    init_db(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Blueprints registrieren
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(termine_bp)
    
    # Doppelte Termine bereinigen und aus CSV laden
    with app.app_context():
        cleanup_duplicate_termine(app)
        load_termine_from_csv(app)
    
    # Scheduler für E-Mail-Berichte einrichten (nur im Produktionsmodus)
    # Nur starten wenn nicht im Debug-Modus und nur im Hauptprozess (nicht in Gunicorn-Workern)
    if not app.debug:
        import sys
        is_gunicorn = 'gunicorn' in sys.modules
        is_main_process = os.environ.get('SCHEDULER_STARTED') is None
        if not is_gunicorn or is_main_process:
            os.environ['SCHEDULER_STARTED'] = '1'
            setup_scheduler(app)
    
    return app


# Anwendung erstellen
app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
