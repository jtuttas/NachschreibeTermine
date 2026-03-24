import msal
from flask import redirect, url_for, session, request, current_app
from flask_login import LoginManager, login_user, logout_user, current_user
from functools import wraps
from models import User, db

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bitte melden Sie sich an, um auf diese Seite zuzugreifen.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    """Lädt den Benutzer anhand der ID"""
    return User.query.get(int(user_id))


def build_msal_app(cache=None):
    """Erstellt eine MSAL-Anwendung"""
    return msal.ConfidentialClientApplication(
        current_app.config['AZURE_CLIENT_ID'],
        authority=current_app.config['AZURE_AUTHORITY'],
        client_credential=current_app.config['AZURE_CLIENT_SECRET'],
        token_cache=cache
    )


def get_auth_url():
    """Generiert die Azure AD Authentifizierungs-URL"""
    msal_app = build_msal_app()
    redirect_uri = request.url_root.rstrip('/') + current_app.config['AZURE_REDIRECT_PATH']
    
    auth_url = msal_app.get_authorization_request_url(
        current_app.config['AZURE_SCOPE'],
        redirect_uri=redirect_uri,
        state=session.get('state', '')
    )
    return auth_url


def get_token_from_code(code):
    """Tauscht den Autorisierungscode gegen ein Token"""
    msal_app = build_msal_app()
    redirect_uri = request.url_root.rstrip('/') + current_app.config['AZURE_REDIRECT_PATH']
    
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=current_app.config['AZURE_SCOPE'],
        redirect_uri=redirect_uri
    )
    return result


def get_user_info(access_token):
    """Ruft Benutzerinformationen von Microsoft Graph ab"""
    import requests
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
    
    if response.status_code == 200:
        return response.json()
    return None


def check_group_membership(access_token, group_name_or_id=None):
    """Überprüft ob der Benutzer Mitglied einer bestimmten Gruppe ist.
    
    Args:
        access_token: OAuth2 Access Token
        group_name_or_id: Gruppenname oder Gruppen-Object-ID (aus Azure AD)
    
    Returns:
        True wenn Benutzer Mitglied ist, sonst False
    """
    import requests
    
    if not group_name_or_id:
        group_name_or_id = current_app.config.get('AZURE_ALLOWED_GROUP', 'Lehrer')
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(
        'https://graph.microsoft.com/v1.0/me/memberOf',
        headers=headers
    )
    
    if response.status_code == 200:
        groups = response.json().get('value', [])
        for group in groups:
            # Prüfe sowohl displayName als auch ID
            if group.get('displayName') == group_name_or_id or group.get('id') == group_name_or_id:
                return True
    return False


def lehrer_required(f):
    """Decorator der sicherstellt, dass der Benutzer ein Lehrer ist"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Debug-Benutzer haben Zugriff auf Debug-Funktionen
        if current_user.is_test_user:
            return f(*args, **kwargs)
        
        # Normale Benutzer müssen Lehrer sein
        if not current_user.is_lehrer:
            return redirect(url_for('main.unauthorized'))
        
        return f(*args, **kwargs)
    return decorated_function


def create_or_update_user(user_info, is_lehrer=True):
    """Erstellt oder aktualisiert einen Benutzer basierend auf Azure AD-Informationen"""
    azure_id = user_info.get('id')
    email = user_info.get('mail') or user_info.get('userPrincipalName')
    name = user_info.get('displayName', email)
    
    user = User.query.filter_by(azure_id=azure_id).first()
    
    if not user:
        user = User.query.filter_by(email=email).first()
    
    if user:
        # Benutzer aktualisieren
        user.azure_id = azure_id
        user.name = name
        user.is_lehrer = is_lehrer
    else:
        # Neuen Benutzer erstellen
        user = User(
            email=email,
            name=name,
            azure_id=azure_id,
            is_lehrer=is_lehrer
        )
        db.session.add(user)
    
    db.session.commit()
    return user
