import logging
import os
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from flask import current_app
from flask_mail import Mail, Message

mail = Mail()

# Module-level reference to prevent garbage collection of the scheduler
_scheduler = None


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
        print(f'[E-Mail] Fehler beim Senden an {to}: {str(e)}', flush=True)
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
    global _scheduler
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
    from models import Termin

    berlin_tz = ZoneInfo('Europe/Berlin')
    scheduler = BackgroundScheduler(timezone=berlin_tz)

    def send_daily_reports():
        """Sendet Tagesberichte für alle Termine des Tages"""
        try:
            with app.app_context():
                heute = datetime.now(berlin_tz).date()
                print(f'[Scheduler] Tagesbericht-Job gestartet für {heute}', flush=True)
                app.logger.info(f'Scheduler: Suche Termine für {heute}...')
                termine = Termin.query.filter_by(datum=heute).all()
                print(f'[Scheduler] {len(termine)} Termine gefunden für {heute}', flush=True)
                app.logger.info(f'Scheduler: {len(termine)} Termine gefunden.')

                for termin in termine:
                    try:
                        buchungen = termin.buchungen.all()
                        if buchungen:
                            send_tagesbericht(termin, buchungen)
                            print(f'[Scheduler] Tagesbericht für {termin.datum} gesendet.', flush=True)
                            app.logger.info(f'Tagesbericht für {termin.datum} gesendet.')
                    except Exception as e:
                        print(f'[Scheduler] Fehler für Termin {termin.datum}: {e}', flush=True)
                        app.logger.error(f'Scheduler Fehler für Termin {termin.datum}: {str(e)}')
        except Exception as e:
            print(f'[Scheduler] Kritischer Fehler in send_daily_reports: {e}', flush=True)
            import traceback
            traceback.print_exc()

    def job_listener(event):
        """Protokolliert APScheduler Job-Ausführungen und Fehler"""
        if event.exception:
            print(f'[Scheduler] Job "{event.job_id}" fehlgeschlagen: {event.exception}', flush=True)
        else:
            print(f'[Scheduler] Job "{event.job_id}" erfolgreich ausgeführt.', flush=True)

    scheduler.add_listener(job_listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)

    # APScheduler-eigene Fehlermeldungen auf stdout weiterleiten
    logging.getLogger('apscheduler').setLevel(logging.WARNING)

    # Jeden Tag um 23:59 Uhr (Europe/Berlin) ausführen
    scheduler.add_job(
        send_daily_reports,
        CronTrigger(hour=23, minute=59, timezone=berlin_tz),
        id='daily_report',
        replace_existing=True,
        # Grace period of 1 hour: allows the job to fire even if the scheduler
        # was briefly unavailable at 23:59 (e.g., container restart or high load).
        # Since the job only queries today's date, firing up to 00:59 still reports
        # the correct day's termine.
        misfire_grace_time=3600,
    )

    scheduler.start()

    # Store at module level to prevent garbage collection
    _scheduler = scheduler

    print(f'[Scheduler] Tagesberichts-Scheduler gestartet (PID: {os.getpid()})', flush=True)
    app.logger.info('Scheduler für Tagesberichte gestartet.')

    return scheduler
