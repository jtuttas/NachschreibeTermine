import csv
import os
from datetime import datetime, date, time
from io import BytesIO

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, send_file
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, PasswordField, URLField, SelectField, ValidationError
from wtforms.validators import DataRequired, Optional, NumberRange, URL, Length

from models import db, User, Termin, Buchung
from auth import (
    get_auth_url, get_token_from_code, get_user_info, 
    check_group_membership, create_or_update_user, lehrer_required
)

# Blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
main_bp = Blueprint('main', __name__)
termine_bp = Blueprint('termine', __name__, url_prefix='/termine')


# --- Formulare ---

class LoginForm(FlaskForm):
    """Formular für Debug-Login"""
    username = StringField('Benutzername', validators=[DataRequired()])
    password = PasswordField('Passwort', validators=[DataRequired()])


class BuchungForm(FlaskForm):
    """Formular für Schülerbuchung"""
    schueler_name = StringField('Name des Schülers', validators=[DataRequired(), Length(max=100)])
    klasse = StringField('Klasse', validators=[Optional(), Length(max=20)])
    dauer_minuten = IntegerField('Dauer (Minuten)', validators=[DataRequired(), NumberRange(min=15, max=300)], default=90)
    ist_digital = BooleanField('Digitale Klassenarbeit (Moodle)')
    moodle_url = URLField('Moodle-Kurs URL', validators=[Optional(), URL()])
    moodle_passwort = StringField('Moodle Passwort', validators=[Optional(), Length(max=100)])
    
    def validate_moodle_url(self, field):
        """Moodle-URL ist Pflicht bei digitaler Klassenarbeit"""
        if self.ist_digital.data and not field.data:
            raise ValidationError('Bei einer digitalen Klassenarbeit ist die Moodle-URL erforderlich.')


# --- Auth Routes ---

@auth_bp.route('/login')
def login():
    """Zeigt die Login-Seite"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    return render_template('auth/login.html', form=form)


@auth_bp.route('/login/azure')
def login_azure():
    """Startet den Azure AD Login"""
    session['state'] = os.urandom(16).hex()
    auth_url = get_auth_url()
    return redirect(auth_url)


@auth_bp.route('/login/debug', methods=['POST'])
def login_debug():
    """Debug-Login mit Benutzername und Passwort"""
    if not current_app.config['DEBUG_MODE']:
        flash('Debug-Login ist deaktiviert.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email='user@test.local').first()
        
        if user and user.check_password(form.password.data) and form.username.data == 'user':
            login_user(user)
            flash('Erfolgreich als Testbenutzer angemeldet.', 'success')
            return redirect(url_for('main.dashboard'))
        
        flash('Ungültige Anmeldedaten.', 'danger')
    
    return redirect(url_for('auth.login'))


@auth_bp.route('/callback')
def callback():
    """Callback für Azure AD Authentifizierung"""
    code = request.args.get('code')
    
    if not code:
        flash('Authentifizierung fehlgeschlagen.', 'danger')
        return redirect(url_for('auth.login'))
    
    try:
        result = get_token_from_code(code)
        
        if 'access_token' not in result:
            flash('Token-Abruf fehlgeschlagen.', 'danger')
            return redirect(url_for('auth.login'))
        
        access_token = result['access_token']
        user_info = get_user_info(access_token)
        
        if not user_info:
            flash('Benutzerinformationen konnten nicht abgerufen werden.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Prüfen ob Benutzer in der Lehrer-Gruppe ist
        is_lehrer = check_group_membership(access_token, 'Lehrer')
        
        if not is_lehrer:
            flash('Sie sind nicht Mitglied der Lehrer-Gruppe.', 'danger')
            return redirect(url_for('auth.login'))
        
        user = create_or_update_user(user_info, is_lehrer)
        login_user(user)
        
        flash(f'Willkommen, {user.name}!', 'success')
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        current_app.logger.error(f'Auth callback error: {str(e)}')
        flash('Ein Fehler ist aufgetreten.', 'danger')
        return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
@login_required
def logout():
    """Meldet den Benutzer ab"""
    logout_user()
    session.clear()
    flash('Sie wurden erfolgreich abgemeldet.', 'info')
    return redirect(url_for('auth.login'))


# --- Main Routes ---

@main_bp.route('/')
def index():
    """Startseite"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
@lehrer_required
def dashboard():
    """Dashboard mit Terminübersicht"""
    heute = date.today()
    
    # Termine die noch nicht vergangen sind
    termine = Termin.query.filter(
        Termin.datum >= heute
    ).order_by(Termin.datum, Termin.uhrzeit).all()
    
    # Gruppiere Termine nach Datum
    termine_gruppiert = {}
    for termin in termine:
        datum_key = termin.datum.strftime('%Y-%m-%d')
        if datum_key not in termine_gruppiert:
            termine_gruppiert[datum_key] = {
                'datum': termin.datum,
                'termine': []
            }
        termine_gruppiert[datum_key]['termine'].append(termin)
    
    # Eigene Buchungen
    meine_buchungen = Buchung.query.filter_by(lehrer_id=current_user.id).join(Termin).filter(
        Termin.datum >= heute
    ).order_by(Termin.datum, Termin.uhrzeit).all()
    
    max_plaetze = current_app.config['MAX_SCHUELER_PRO_TERMIN']
    
    # Anzahl verfügbarer Termine berechnen
    total_termine = len(termine)
    
    return render_template('dashboard.html', 
                         termine_gruppiert=termine_gruppiert,
                         meine_buchungen=meine_buchungen,
                         max_plaetze=max_plaetze,
                         heute=heute,
                         total_termine=total_termine)


@main_bp.route('/unauthorized')
def unauthorized():
    """Seite für nicht autorisierte Benutzer"""
    return render_template('unauthorized.html'), 403


# --- Termine Routes ---

@termine_bp.route('/<int:termin_id>')
@login_required
@lehrer_required
def detail(termin_id):
    """Detailansicht eines Termins"""
    termin = Termin.query.get_or_404(termin_id)
    buchungen = termin.buchungen.all()
    max_plaetze = current_app.config['MAX_SCHUELER_PRO_TERMIN']
    
    return render_template('termine/detail.html', 
                         termin=termin, 
                         buchungen=buchungen,
                         max_plaetze=max_plaetze)


@termine_bp.route('/<int:termin_id>/buchen', methods=['GET', 'POST'])
@login_required
@lehrer_required
def buchen(termin_id):
    """Schüler für einen Termin buchen"""
    termin = Termin.query.get_or_404(termin_id)
    max_plaetze = current_app.config['MAX_SCHUELER_PRO_TERMIN']
    
    # Prüfen ob Termin noch buchbar ist (nicht heute und nicht vergangen)
    if not termin.ist_buchbar:
        flash('Für diesen Termin können keine Buchungen mehr vorgenommen werden.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Prüfen ob noch Plätze frei sind
    if not termin.hat_freie_plaetze(max_plaetze):
        flash('Für diesen Termin sind keine Plätze mehr frei.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    form = BuchungForm()
    
    if form.validate_on_submit():
        buchung = Buchung(
            termin_id=termin.id,
            lehrer_id=current_user.id,
            schueler_name=form.schueler_name.data,
            klasse=form.klasse.data,
            dauer_minuten=form.dauer_minuten.data,
            ist_digital=form.ist_digital.data,
            moodle_url=form.moodle_url.data if form.ist_digital.data else None,
            moodle_passwort=form.moodle_passwort.data if form.ist_digital.data else None
        )
        
        db.session.add(buchung)
        db.session.commit()
        
        flash(f'{form.schueler_name.data} wurde erfolgreich für den Termin eingetragen.', 'success')
        return redirect(url_for('termine.detail', termin_id=termin.id))
    
    return render_template('termine/buchen.html', form=form, termin=termin)


@termine_bp.route('/buchung/<int:buchung_id>/bearbeiten', methods=['GET', 'POST'])
@login_required
@lehrer_required
def buchung_bearbeiten(buchung_id):
    """Buchung bearbeiten"""
    buchung = Buchung.query.get_or_404(buchung_id)
    
    # Nur eigene Buchungen bearbeiten
    if buchung.lehrer_id != current_user.id:
        flash('Sie können nur eigene Buchungen bearbeiten.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Prüfen ob Termin in der Vergangenheit
    if buchung.termin.ist_vergangen:
        flash('Buchungen für vergangene Termine können nicht bearbeitet werden.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    form = BuchungForm(obj=buchung)
    
    if form.validate_on_submit():
        buchung.schueler_name = form.schueler_name.data
        buchung.klasse = form.klasse.data
        buchung.dauer_minuten = form.dauer_minuten.data
        buchung.ist_digital = form.ist_digital.data
        buchung.moodle_url = form.moodle_url.data if form.ist_digital.data else None
        buchung.moodle_passwort = form.moodle_passwort.data if form.ist_digital.data else None
        
        db.session.commit()
        
        flash(f'Buchung für {buchung.schueler_name} wurde aktualisiert.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('termine/buchen.html', form=form, termin=buchung.termin, buchung=buchung, edit_mode=True)


@termine_bp.route('/buchung/<int:buchung_id>/loeschen', methods=['POST'])
@login_required
@lehrer_required
def buchung_loeschen(buchung_id):
    """Buchung löschen"""
    buchung = Buchung.query.get_or_404(buchung_id)
    
    # Nur eigene Buchungen löschen
    if buchung.lehrer_id != current_user.id:
        flash('Sie können nur eigene Buchungen löschen.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    schueler_name = buchung.schueler_name
    
    db.session.delete(buchung)
    db.session.commit()
    
    flash(f'Buchung für {schueler_name} wurde gelöscht.', 'success')
    return redirect(url_for('main.dashboard'))


@termine_bp.route('/<int:termin_id>/teilnehmerliste')
@login_required
@lehrer_required
def teilnehmerliste(termin_id):
    """Teilnehmerliste für einen Termin"""
    termin = Termin.query.get_or_404(termin_id)
    buchungen = termin.buchungen.all()
    
    # Prüfen ob heute der Tag des Termins ist
    ist_heute = termin.datum == datetime.now().date()
    
    return render_template('termine/teilnehmerliste.html', 
                         termin=termin, 
                         buchungen=buchungen,
                         ist_heute=ist_heute)


@termine_bp.route('/buchung/<int:buchung_id>/anwesenheit', methods=['POST'])
@login_required
@lehrer_required
def anwesenheit_toggle(buchung_id):
    """Anwesenheit eines Schülers umschalten"""
    buchung = Buchung.query.get_or_404(buchung_id)
    
    # Prüfen ob heute der Tag des Termins ist
    if buchung.termin.datum != datetime.now().date():
        flash('Anwesenheit kann nur am Tag des Termins bestätigt werden.', 'danger')
        return redirect(url_for('termine.teilnehmerliste', termin_id=buchung.termin_id))
    
    buchung.ist_anwesend = not buchung.ist_anwesend
    if buchung.ist_anwesend:
        buchung.anwesenheit_bestaetigt_um = datetime.now()
    else:
        buchung.anwesenheit_bestaetigt_um = None
    
    db.session.commit()
    
    status = 'anwesend' if buchung.ist_anwesend else 'abwesend'
    flash(f'{buchung.schueler_name} als {status} markiert.', 'success')
    
    return redirect(url_for('termine.teilnehmerliste', termin_id=buchung.termin_id))


@termine_bp.route('/<int:termin_id>/pdf')
@login_required
@lehrer_required
def teilnehmerliste_pdf(termin_id):
    """Exportiert die Teilnehmerliste als PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    
    termin = Termin.query.get_or_404(termin_id)
    buchungen = termin.buchungen.all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center
    )
    
    elements = []
    
    # Titel
    titel = f"Nachschreibetermin - {termin.datum.strftime('%d.%m.%Y')} um {termin.uhrzeit.strftime('%H:%M')}"
    elements.append(Paragraph(titel, title_style))
    
    # Info
    info = f"Raum: {termin.raum or 'N/A'} | Aufsicht: {termin.aufsicht_email}"
    elements.append(Paragraph(info, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    if buchungen:
        # Tabellendaten
        data = [['#', 'Name', 'Klasse', 'Dauer', 'Digital', 'Anw.']]
        
        for i, buchung in enumerate(buchungen, 1):
            # Anwesenheitssymbol: Häkchen für anwesend, X für abwesend
            if buchung.ist_anwesend:
                anwesend_symbol = '✓'
            else:
                anwesend_symbol = '✗'
            
            data.append([
                str(i),
                buchung.schueler_name,
                buchung.klasse or '-',
                f'{buchung.dauer_minuten} Min.',
                'Ja' if buchung.ist_digital else 'Nein',
                anwesend_symbol
            ])
        
        # Tabelle erstellen
        table = Table(data, colWidths=[1*cm, 5.5*cm, 2*cm, 2.5*cm, 1.5*cm, 1.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(table)
    else:
        elements.append(Paragraph("Keine Schüler für diesen Termin eingetragen.", styles['Normal']))
    
    # PDF erstellen
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"Teilnehmerliste_{termin.datum.strftime('%Y%m%d')}_{termin.uhrzeit.strftime('%H%M')}.pdf"
    
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')


# --- Hilfsfunktionen ---

def load_termine_from_csv(app):
    """Lädt Termine aus einer CSV-Datei und synchronisiert mit der Datenbank.
    
    - Neue Termine aus der CSV werden hinzugefügt
    - Termine ohne Buchungen, die nicht mehr in der CSV sind, werden entfernt
    - Termine mit Buchungen bleiben erhalten (auch wenn nicht in CSV)
    """
    csv_path = app.config['TERMINE_CSV_PATH']
    
    if not os.path.exists(csv_path):
        app.logger.warning(f'CSV-Datei nicht gefunden: {csv_path}')
        return 0
    
    # Sammle alle Termine aus der CSV
    csv_termine = set()
    new_termine = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                datum = datetime.strptime(row['datum'], '%Y-%m-%d').date()
                uhrzeit = datetime.strptime(row['uhrzeit'], '%H:%M').time()
                csv_termine.add((datum, uhrzeit))
                
                # Prüfen ob Termin bereits existiert
                existing = Termin.query.filter_by(
                    datum=datum,
                    uhrzeit=uhrzeit
                ).first()
                
                if not existing:
                    termin = Termin(
                        datum=datum,
                        uhrzeit=uhrzeit,
                        aufsicht_email=row['aufsicht_email'],
                        raum=row.get('raum')
                    )
                    db.session.add(termin)
                    new_termine.append(termin)
                    
            except Exception as e:
                app.logger.error(f'Fehler beim Laden des Termins: {str(e)}')
    
    # Entferne Termine die nicht mehr in der CSV sind (nur ohne Buchungen)
    removed_count = 0
    if csv_termine:  # Nur synchronisieren wenn CSV Termine enthält
        all_termine = Termin.query.all()
        for termin in all_termine:
            termin_key = (termin.datum, termin.uhrzeit)
            if termin_key not in csv_termine:
                if termin.buchungen.count() == 0:
                    db.session.delete(termin)
                    removed_count += 1
                else:
                    app.logger.info(f'Termin {termin.datum} {termin.uhrzeit} nicht in CSV, aber hat Buchungen - wird beibehalten')
    else:
        # CSV ist leer - entferne alle Termine ohne Buchungen
        all_termine = Termin.query.all()
        for termin in all_termine:
            if termin.buchungen.count() == 0:
                db.session.delete(termin)
                removed_count += 1
    
    db.session.commit()
    app.logger.info(f'{len(new_termine)} Termine aus CSV geladen, {removed_count} veraltete Termine entfernt.')
    return len(new_termine)
