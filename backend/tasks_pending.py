# tasks.py
import os
import csv
import io
from datetime import datetime, timedelta,timezone
from celery import shared_task
from sqlalchemy import func
from celery_app import celery
from backend.app import create_app, db  # adapt to your app factory
from backend.models import User, ParkingLot, Reservation, ParkingSpot
from jinja2 import Template
import smtplib
from email.message import EmailMessage
import requests

app = create_app()
app.app_context().push()

# ---- Helpers: email and google chat webhook ----
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.example.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "no-reply@example.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "changeme")

google_chat_webhook = "https://chat.googleapis.com/v1/spaces/AAQAwtQ63ag/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=5MYSUrPN6reLnOlxNcejvgkOJ35PtxS2QRY6c_FTM7c"

def send_email(to_email, subject, html_body, attachments=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg.set_content("This email contains HTML. Please open in an HTML-capable client.")
    msg.add_alternative(html_body, subtype='html')
    if attachments:
        for attach in attachments:
            filename, content, mime = attach
            msg.add_attachment(content, maintype=mime.split('/')[0], subtype=mime.split('/')[1], filename=filename)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

def send_google_chat(webhook_url, text):
    payload = {"text": text}
    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception as e:
        app.logger.exception("Failed to send Google Chat message: %s", e)

# ---- Query helpers ----
def users_to_remind(days_inactive=7):
    """
    Return users who haven't visited in `days_inactive` days OR for whom admin created parking lot recently.
    Adjust logic as required.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_inactive)
    # users with last reservation older than cutoff OR never reserved
    sub = db.session.query(Reservation.user_id, func.max(Reservation.created_at).label('last_visit')).group_by(Reservation.user_id).subquery()
    q = db.session.query(User).outerjoin(sub, User.id == sub.c.user_id).filter(
        (sub.c.last_visit == None) | (sub.c.last_visit < cutoff)
    )
    return q.all()

def users_with_new_parking_lot(since_days=7):
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    # If any parking lot created since cutoff, notify all users who haven't visited recently (or all users by policy)
    lots = ParkingLot.query.filter(ParkingLot.created_at >= cutoff).all()
    if not lots:
        return []
    return User.query.all()

# ---- Tasks ----

@shared_task(name='tasks.daily_reminder_runner')
def daily_reminder_runner():

    now_utc = datetime.now(timezone.utc) 
    # convert to IST offset if needed; we can store user.preferred_reminder_time as "HH:MM" in user's timezone
    users = User.query.filter(User.active==True).all()
    for u in users:
        if not u.receive_reminders:  # boolean flag
            continue
        # assume u.reminder_time is stored as "18:00" (HH:MM) in user's timezone Asia/Kolkata
        pref = getattr(u, "reminder_time", "18:00")
        pref_hour, pref_min = map(int, pref.split(":"))
        # convert now_utc to IST hour:
        from pytz import timezone, utc
        ist = timezone("Asia/Kolkata")
        now_ist = utc.localize(now_utc).astimezone(ist)
        if now_ist.hour == pref_hour and now_ist.minute == pref_min:
            # decide if they should be reminded
            last_res = Reservation.query.filter_by(user_id=u.id).order_by(Reservation.created_at.desc()).first()
            send_if_no_visit = False
            if not last_res:
                send_if_no_visit = True
            else:
                days = (now_utc - last_res.created_at).days
                if days >= 7:  # example threshold
                    send_if_no_visit = True

            # or if admin created a parking lot recently
            recent_lot = ParkingLot.query.filter(ParkingLot.created_at >= now_utc - timedelta(days=7)).first()
            if send_if_no_visit or recent_lot:
                message = f"Hi {u.name}, we noticed you haven't booked parking recently. If you need a spot tonight, book now!"
                # preference: google_chat_webhook_url stored on User model OR fallback to email
                if getattr(u, "google_chat_webhook", None):
                    send_google_chat(u.google_chat_webhook, message)
                else:
                    send_email(u.email, "Parking reminder", f"<p>{message}</p>")

@shared_task(name='tasks.monthly_report_runner')
def monthly_report_runner():
    """
    Run on 1st of month -> create and email reports for all users.
    """
    # For each user, generate HTML report and email
    now = datetime.now(timezone.utc)
    # month range: previous month
    first_of_this_month = datetime(now.year, now.month, 1)
    import calendar
    prev_month_last_day = first_of_this_month - timedelta(days=1)
    prev_month = prev_month_last_day.month
    prev_year = prev_month_last_day.year
    start_period = datetime(prev_year, prev_month, 1)
    end_period = datetime(prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1], 23, 59, 59)

    users = User.query.filter(User.active==True).all()
    for u in users:
        # gather stats
        reservations = Reservation.query.filter(
            Reservation.user_id == u.id,
            Reservation.created_at >= start_period,
            Reservation.created_at <= end_period
        ).all()
        total_booked = len(reservations)
        amount_spent = sum(r.cost for r in reservations if getattr(r, "parking_fee", None) is not None)
        # most used lot
        from collections import Counter
        lot_ids = [r.spot.lot_id for r in reservations if hasattr(r, "parking_lot_id")]
        most_used = None
        if lot_ids:
            counted = Counter(lot_ids).most_common(1)
            most_used = ParkingLot.query.get(counted[0][0]).name if counted else None

        # Render HTML (simple template)
        template = Template("""
        <h2>Monthly Parking Report — {{ month_year }}</h2>
        <p>Hello {{ user.name }},</p>
        <ul>
          <li>Total bookings: {{ total_booked }}</li>
          <li>Most used parking lot: {{ most_used or "N/A" }}</li>
          <li>Amount spent: ₹{{ amount_spent }}</li>
        </ul>
        <p>Bookings detail:</p>
        <table border="1" cellpadding="6" cellspacing="0">
            <thead><tr><th>Slot</th><th>Parking Lot</th><th>Start</th><th>End</th><th>Cost</th></tr></thead>
            <tbody>
            {% for r in reservations %}
              <tr>
                <td>{{ r.slot_id }}</td>
                <td>{{ r.parking_lot.name if r.parking_lot else r.parking_lot_id }}</td>
                <td>{{ r.start_time }}</td>
                <td>{{ r.end_time }}</td>
                <td>{{ r.cost or "-" }}</td>
              </tr>
            {% endfor %}
            </tbody>
        </table>
        <p>Regards,<br/>Parking App</p>
        """)
        html = template.render(
            month_year=f"{calendar.month_name[prev_month]} {prev_year}",
            user=u,
            total_booked=total_booked,
            most_used=most_used,
            amount_spent=amount_spent,
            reservations=reservations
        )

        # send email
        try:
            send_email(u.email, f"Your Parking Activity Report — {calendar.month_name[prev_month]} {prev_year}", html)
        except Exception as e:
            app.logger.exception("Failed to send monthly report to %s: %s", u.email, e)


@shared_task(name='tasks.generate_export_csv')
def generate_export_csv(user_id):
    """
    Creates CSV with all reservations for a user and stores it.
    Returns URL/path to the file.
    """
    u = User.query.get(user_id)
    if not u:
        return {"error": "user not found"}

    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.created_at.asc()).all()

    # create CSV in-memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["reservation_id", "slot_id", "spot_id", "parking_lot", "start_time", "end_time", "created_at", "cost", "remarks"])
    for r in reservations:
        writer.writerow([
            getattr(r, 'id', ''),
            getattr(r, 'slot_id', ''),
            getattr(r, 'parking_spot_id', ''),  # adapt field names
            r.parking_lot.name if getattr(r, 'parking_lot', None) else getattr(r, 'parking_lot_id', ''),
            getattr(r, 'start_time', ''),
            getattr(r, 'end_time', ''),
            getattr(r, 'created_at', ''),
            getattr(r, 'cost', ''),
            getattr(r, 'remarks', '')
        ])

    csv_content = output.getvalue().encode('utf-8')
    output.close()

    # Store file: dev use local path, prod use S3
    filename = f"user_{user_id}_reservations_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv"
    storage_dir = os.environ.get("REPORT_STORAGE_DIR", "uploads/reports")
    os.makedirs(storage_dir, exist_ok=True)
    file_path = os.path.join(storage_dir, filename)
    with open(file_path, "wb") as f:
        f.write(csv_content)

    # Optionally: if using S3, upload and create signed URL here

    # Notify user via email / google chat
    link = f"{os.environ.get('APP_BASE_URL','http://localhost:5000')}/reports/{filename}"  # ensure you serve files in dev
    message = f"Your CSV export is ready: {link}"
    if getattr(u, "google_chat_webhook", None):
        send_google_chat(u.google_chat_webhook, message)
    send_email(u.email, "Your Parking CSV Export is ready", f"<p>{message}</p>")

    return {"status": "ok", "file": file_path, "url": link}


# Replace field names with your actual model fields.

# Use pytz (or Python 3.9+ zones) to handle IST conversion.

# For production, upload CSV to S3 and return a presigned URL.


#  google_chat_webhook = https://chat.googleapis.com/v1/spaces/AAQAwtQ63ag/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=5MYSUrPN6reLnOlxNcejvgkOJ35PtxS2QRY6c_FTM7c
