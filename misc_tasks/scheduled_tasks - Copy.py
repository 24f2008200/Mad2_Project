# backend/tasks/scheduled_tasks.py
import os
import io
import csv
import calendar
from datetime import datetime, timedelta, timezone
from jinja2 import Template
from celery import shared_task
from backend.celery_app import celery
from backend.app import create_app, db,my_app
from backend.models import User, ParkingLot, Reservation,ReminderJob
from backend.services.mail_utils import send_email
from backend.services.chat_utils import send_google_chat
from backend.services.user_queries import users_to_remind, users_with_new_parking_lot, build_reminder_message
from pytz import timezone, utc


# Setup app context for DB access
app = my_app or create_app()
app.app_context().push()

@shared_task
def daily_reminder_planner():
    ist = timezone("Asia/Kolkata")

    users = User.query.filter(User.active == True,
                              User.receive_reminders == True).all()

    for u in users:
        if not qualifies_for_reminder(u):
            continue

        # user's preferred time in IST
        hh, mm = map(int, u.reminder_time.split(":"))
        today_ist = datetime.now(ist).replace(hour=hh, minute=mm, second=0, microsecond=0)

        # convert to UTC for DB storage
        scheduled_utc = today_ist.astimezone(timezone.utc)

        job = ReminderJob(user_id=u.id, scheduled_at=scheduled_utc)
        db.session.add(job)

    db.session.commit()

def qualifies_for_reminder(user):
    """Check if user qualifies for a reminder based on activity and new parking lots."""
    last_res = (
        Reservation.query.filter_by(user_id=user.id)
        .order_by(Reservation.created_at.desc())
        .first()
    )

    inactive = not last_res or (datetime.now(timezone.utc) - last_res.created_at).days >= 7
    recent_lot = ParkingLot.query.filter(
        ParkingLot.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
    ).first()

    return inactive or recent_lot is not None

@shared_task
def minute_reminder_executor():
    now_utc = datetime.now(timezone.utc)

    jobs = ReminderJob.query.filter(
        ReminderJob.status == "pending",
        ReminderJob.scheduled_at <= now_utc
    ).all()

    for job in jobs:
        u = User.query.get(job.user_id)

        # Re-check eligibility (optional but recommended)
        if not qualifies_for_reminder(u):
            job.status = "skipped"
        else:
            send_reminder(u)
            job.status = "sent"
            job.sent_at = now_utc

    db.session.commit()
def send_reminder(user):
    """Send reminder to user via email or Google Chat."""
    message = build_reminder_message(user)

    if getattr(user, "google_chat_webhook", None):
        send_google_chat(user.google_chat_webhook, message)
    else:
        send_email(user.email, "Parking reminder", f"<p>{message}</p>")


@shared_task(name="tasks.daily_reminder_runner")
def daily_reminder_runner():
    now_utc = datetime.now(timezone.utc)
    ist = timezone("Asia/Kolkata")
    now_ist = utc.localize(now_utc).astimezone(ist)

    users = User.query.filter(User.active == True).all()

    for u in users:
        if not u.receive_reminders:
            continue

        pref_hour, pref_min = map(int, getattr(u, "reminder_time", "18:00").split(":"))

        # Skip if already sent today
        if u.last_reminder_sent_at:
            last_ist = utc.localize(u.last_reminder_sent_at).astimezone(ist)
            if last_ist.date() == now_ist.date():
                continue

        if now_ist.hour == pref_hour and now_ist.minute == pref_min:
            last_res = (
                Reservation.query.filter_by(user_id=u.id)
                .order_by(Reservation.created_at.desc())
                .first()
            )

            inactive = not last_res or (now_utc - last_res.created_at).days >= 7
            recent_lot = ParkingLot.query.filter(
                ParkingLot.created_at >= now_utc - timedelta(days=7)
            ).first()

            if inactive or recent_lot:
                message = build_reminder_message(u)

                if getattr(u, "google_chat_webhook", None):
                    send_google_chat(u.google_chat_webhook, message)
                else:
                    send_email(u.email, "Parking reminder", f"<p>{message}</p>")

                #  Mark reminder sent
                u.last_reminder_sent_at = now_utc
                db.session.commit()


@shared_task(name="tasks.monthly_report_runner")
def monthly_report_runner():
    """Generate and email monthly reports for all users."""
    now = datetime.now(timezone.utc)
    first_of_this_month = datetime(now.year, now.month, 1)
    prev_month_last_day = first_of_this_month - timedelta(days=1)
    prev_month = prev_month_last_day.month
    prev_year = prev_month_last_day.year
    start_period = datetime(prev_year, prev_month, 1)
    end_period = datetime(
        prev_year,
        prev_month,
        calendar.monthrange(prev_year, prev_month)[1],
        23,
        59,
        59,
    )

    users = User.query.filter(User.active == True).all()
    for u in users:
        reservations = Reservation.query.filter(
            Reservation.user_id == u.id,
            Reservation.created_at >= start_period,
            Reservation.created_at <= end_period,
        ).all()

        total_booked = len(reservations)
        amount_spent = sum(getattr(r, "cost", 0) for r in reservations)
        lot_names = [r.parking_lot.name for r in reservations if r.parking_lot]
        most_used = max(set(lot_names), key=lot_names.count) if lot_names else None

        template = Template("""
        <h2>Monthly Parking Report — {{ month_year }}</h2>
        <p>Hello {{ user.name }},</p>
        <ul>
          <li>Total bookings: {{ total_booked }}</li>
          <li>Most used parking lot: {{ most_used or "N/A" }}</li>
          <li>Amount spent: ₹{{ amount_spent }}</li>
        </ul>
        """)
        html = template.render(
            month_year=f"{calendar.month_name[prev_month]} {prev_year}",
            user=u,
            total_booked=total_booked,
            most_used=most_used,
            amount_spent=amount_spent,
        )

        send_email(u.email, f"Your Parking Report — {calendar.month_name[prev_month]} {prev_year}", html)


@shared_task(name="tasks.generate_export_csv")
def generate_export_csv(user_id):
    """Export a user's reservations to a CSV and email the link."""
    u = User.query.get(user_id)
    if not u:
        return {"error": "User not found"}

    reservations = Reservation.query.filter_by(user_id=user_id).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "slot_id", "lot", "start_time", "end_time", "cost"])
    for r in reservations:
        writer.writerow([
            r.id,
            getattr(r, "slot_id", ""),
            getattr(r.parking_lot, "name", ""),
            r.start_time,
            r.end_time,
            getattr(r, "cost", ""),
        ])

    csv_bytes = output.getvalue().encode("utf-8")
    output.close()

    filename = f"user_{user_id}_reservations_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv"
    storage_dir = os.environ.get("REPORT_STORAGE_DIR", "uploads/reports")
    os.makedirs(storage_dir, exist_ok=True)
    file_path = os.path.join(storage_dir, filename)

    with open(file_path, "wb") as f:
        f.write(csv_bytes)

    link = f"{os.environ.get('APP_BASE_URL','http://localhost:5000')}/reports/{filename}"
    message = f"Your CSV export is ready: {link}"

    if getattr(u, "google_chat_webhook", None):
        send_google_chat(u.google_chat_webhook, message)
    send_email(u.email, "Your Parking CSV Export is Ready", f"<p>{message}</p>")

    return {"status": "ok", "file": file_path, "url": link}
