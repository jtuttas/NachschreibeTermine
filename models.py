from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Benutzer-Modell für Lehrkräfte"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    azure_id = db.Column(db.String(100), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)  # Für Debug-Benutzer
    is_test_user = db.Column(db.Boolean, default=False)
    is_lehrer = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Beziehung zu gebuchten Schülern
    buchungen = db.relationship('Buchung', backref='erstellt_von', lazy='dynamic',
                                foreign_keys='Buchung.lehrer_id')
    
    def set_password(self, password):
        """Setzt das Passwort für Debug-Benutzer"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Überprüft das Passwort für Debug-Benutzer"""
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False
    
    def __repr__(self):
        return f'<User {self.email}>'


class Termin(db.Model):
    """Modell für Nachschreibetermine"""
    __tablename__ = 'termine'
    
    id = db.Column(db.Integer, primary_key=True)
    datum = db.Column(db.Date, nullable=False)
    uhrzeit = db.Column(db.Time, nullable=False)
    aufsicht_email = db.Column(db.String(120), nullable=False)
    raum = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Beziehung zu Buchungen
    buchungen = db.relationship('Buchung', backref='termin', lazy='dynamic')
    
    @property
    def datetime(self):
        """Kombiniert Datum und Uhrzeit zu einem datetime-Objekt"""
        return datetime.combine(self.datum, self.uhrzeit)
    
    @property
    def ist_vergangen(self):
        """Prüft ob der Termin in der Vergangenheit liegt"""
        return self.datetime < datetime.now()
    
    @property
    def ist_buchbar(self):
        """Prüft ob der Termin buchbar ist (nicht heute und nicht vergangen)"""
        from datetime import date
        # Am Tag selbst können keine Termine mehr eingetragen werden
        return self.datum > date.today()
    
    @property
    def anzahl_buchungen(self):
        """Gibt die Anzahl der Buchungen für diesen Termin zurück"""
        return self.buchungen.count()
    
    def hat_freie_plaetze(self, max_plaetze):
        """Prüft ob noch freie Plätze verfügbar sind"""
        return self.anzahl_buchungen < max_plaetze
    
    def __repr__(self):
        return f'<Termin {self.datum} {self.uhrzeit}>'


class Buchung(db.Model):
    """Modell für Schülerbuchungen"""
    __tablename__ = 'buchungen'
    
    id = db.Column(db.Integer, primary_key=True)
    termin_id = db.Column(db.Integer, db.ForeignKey('termine.id'), nullable=False)
    lehrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Schülerinformationen
    schueler_name = db.Column(db.String(100), nullable=False)
    klasse = db.Column(db.String(20), nullable=True)
    dauer_minuten = db.Column(db.Integer, nullable=False, default=90)
    
    # Art der Klassenarbeit
    ist_digital = db.Column(db.Boolean, default=False)
    moodle_url = db.Column(db.String(500), nullable=True)
    moodle_passwort = db.Column(db.String(100), nullable=True)
    
    # Teilnahmestatus
    ist_anwesend = db.Column(db.Boolean, default=False)
    anwesenheit_bestaetigt_um = db.Column(db.DateTime, nullable=True)
    
    # Metadaten
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Buchung {self.schueler_name} - {self.termin}>'


def init_db(app):
    """Initialisiert die Datenbank und erstellt Testbenutzer"""
    from sqlalchemy.exc import IntegrityError
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Testbenutzer erstellen falls nicht vorhanden
        test_user = User.query.filter_by(email='user@test.local').first()
        if not test_user:
            try:
                test_user = User(
                    email='user@test.local',
                    name='Test Benutzer',
                    is_test_user=True,
                    is_lehrer=False  # Debug-Benutzer ist kein Lehrer
                )
                test_user.set_password('user')
                db.session.add(test_user)
                db.session.commit()
                print("Testbenutzer 'user' wurde erstellt.")
            except IntegrityError:
                # Bei Race Condition (mehrere Worker) einfach ignorieren
                db.session.rollback()
