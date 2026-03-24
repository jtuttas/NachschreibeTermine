import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Basiskonfiguration für die Anwendung"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///nachschreibetermine.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Azure AD Konfiguration
    AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
    AZURE_CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')
    AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID')
    AZURE_AUTHORITY = os.environ.get('AZURE_AUTHORITY', f"https://login.microsoftonline.com/{os.environ.get('AZURE_TENANT_ID', 'common')}")
    AZURE_REDIRECT_PATH = "/auth/callback"
    AZURE_SCOPE = ["User.Read"]
    
    # E-Mail Konfiguration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Anwendungsparameter
    MAX_SCHUELER_PRO_TERMIN = int(os.environ.get('MAX_SCHUELER_PRO_TERMIN', 30))
    DEBUG_MODE = os.environ.get('DEBUG_MODE', 'False').lower() == 'true'
    
    # CSV Pfad für Termine
    TERMINE_CSV_PATH = os.environ.get('TERMINE_CSV_PATH', 'termine.csv')


class DevelopmentConfig(Config):
    """Entwicklungskonfiguration"""
    DEBUG = True


class ProductionConfig(Config):
    """Produktionskonfiguration"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
