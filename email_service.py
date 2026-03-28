from datetime import datetime, date, timedelta
from flask import current_app
from flask_mail import Mail, Message

mail = Mail()


def send_email(to, subject, body_html, body_text=None):
    """Sendet eine E-Mail"""
    try:
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            html=body_html,
            body=body_text or body_html
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'E-Mail Fehler: {str(e)}')
        return False


def send_tagesbericht(termin, buchungen):
    """Sendet den Tagesbericht an alle betroffenen Lehrkräfte"""
    from models import User
    
    # Gruppiere Buchungen nach Lehrkraft
    buchungen_pro_lehrer = {}
    for buchung in buchungen:
        lehrer_id = buchung.lehrer_id
        if lehrer_id not in buchungen_pro_lehrer:
            buchungen_pro_lehrer[lehrer_id] = []
        buchungen_pro_lehrer[lehrer_id].append(buchung)
    
    for lehrer_id, lehrer_buchungen in buchungen_pro_lehrer.items():
        lehrer = User.query.get(lehrer_id)
        if not lehrer or not lehrer.email:
            continue
        
        # E-Mail erstellen
        subject = f"Nachschreibetermin Bericht - {termin.datum.strftime('%d.%m.%Y')}"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4472C4; color: white; }}
                .anwesend {{ color: green; }}
                .abwesend {{ color: red; }}
            </style>
        </head>
        <body>
            <h2>Nachschreibetermin Bericht</h2>
            <p><strong>Datum:</strong> {termin.datum.strftime('%d.%m.%Y')}</p>
            <p><strong>Uhrzeit:</strong> {termin.uhrzeit.strftime('%H:%M')}</p>
            <p><strong>Raum:</strong> {termin.raum or 'N/A'}</p>
            
            <h3>Ihre angemeldeten Schüler:</h3>
            <table>
                <tr>
                    <th>Name</th>
                    <th>Klasse</th>
                    <th>Dauer</th>
                    <th>Art</th>
                    <th>Anwesenheit</th>
                </tr>
        """
        
        for buchung in lehrer_buchungen:
            anwesenheit_class = 'anwesend' if buchung.ist_anwesend else 'abwesend'
            anwesenheit_text = 'Anwesend' if buchung.ist_anwesend else 'NICHT ERSCHIENEN'
            art = 'Digital (Moodle)' if buchung.ist_digital else 'Papier'
            
            html += f"""
                <tr>
                    <td>{buchung.schueler_name}</td>
                    <td>{buchung.klasse or '-'}</td>
                    <td>{buchung.dauer_minuten} Min.</td>
                    <td>{art}</td>
                    <td class="{anwesenheit_class}"><strong>{anwesenheit_text}</strong></td>
                </tr>
            """
        
        html += """
            </table>
            <br>
            <p>Mit freundlichen Grüßen,<br>Ihr Nachschreibetermin-System</p>
        </body>
        </html>
        """
        
        send_email(lehrer.email, subject, html)


def setup_scheduler(app):
    """Richtet den Scheduler für automatische Berichte ein"""
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from models import Termin
    
    scheduler = BackgroundScheduler()
    
    def send_daily_reports():
        """Sendet Tagesberichte für alle Termine des Tages"""
        try:
            with app.app_context():
                heute = date.today()
                app.logger.info(f'Scheduler: Suche Termine für {heute}...')
                termine = Termin.query.filter_by(datum=heute).all()
                app.logger.info(f'Scheduler: {len(termine)} Termine gefunden.')

                for termin in termine:
                    buchungen = termin.buchungen.all()
                    if buchungen:
                        send_tagesbericht(termin, buchungen)
                        app.logger.info(f'Tagesbericht für {termin.datum} gesendet.')
        except Exception as e:
            app.logger.error(f'Scheduler Fehler: {str(e)}')
    
    # Jeden Tag um 23:59 ausführen
    scheduler.add_job(
        send_daily_reports,
        CronTrigger(hour=23, minute=59),
        id='daily_report',
        replace_existing=True
    )
    
    scheduler.start()
    app.logger.info('Scheduler für Tagesberichte gestartet.')
    
    return scheduler
