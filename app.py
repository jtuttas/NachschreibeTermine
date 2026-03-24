import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from config import config
from models import db, init_db
from auth import login_manager
from email_service import mail, setup_scheduler
from routes import auth_bp, main_bp, termine_bp, load_termine_from_csv

csrf = CSRFProtect()


def create_app(config_name=None):
    """Application Factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Extensions initialisieren
    init_db(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Blueprints registrieren
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(termine_bp)
    
    # Termine aus CSV laden
    with app.app_context():
        load_termine_from_csv(app)
    
    # Scheduler für E-Mail-Berichte einrichten (nur im Produktionsmodus)
    if not app.debug:
        setup_scheduler(app)
    
    return app


# Anwendung erstellen
app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
