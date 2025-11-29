# backend/tasks/reminders.py
from datetime import datetime, timedelta, timezone
from pytz import timezone as pytz_tz

from backend.celery_instance import celery



from backend.extensions import db
from backend.models import User, Reservation, ParkingLot, ReminderJob
from backend.services.mail_utils import send_email
from backend.services.chat_utils import send_google_chat
from backend.services.user_queries import build_reminder_message


IST = pytz_tz("Asia/Kolkata")


def qualifies_for_reminder(u):
    last = Reservation.query.filter_by(user_id=u.id)\
           .order_by(Reservation.created_at.desc()).first()
    inactive = not last or (datetime.now(timezone.utc) - last.created_at).days >= 7

    recent_lot = ParkingLot.query.filter(
        ParkingLot.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
    ).first()

    return inactive or recent_lot is not None


# -----------------------------------------------------
# Minute executor
# -----------------------------------------------------
@celery.task(name="backend.tasks.reminders.minute_reminder_executor")
def minute_reminder_executor():
    now_utc = datetime.now(timezone.utc)
    jobs = ReminderJob.query.filter(
        ReminderJob.status == "pending",
        ReminderJob.scheduled_at <= now_utc
    ).all()

    for job in jobs:
        u = User.query.get(job.user_id)
        if not u:
            continue
        if not qualifies_for_reminder(u):
            job.status = "skipped"
        else:
            send_user_reminder(u.id, {"channels": ["email", "gchat"]})
            job.status = "sent"
            job.sent_at = now_utc
    db.session.commit()


# -----------------------------------------------------
# Daily reminder runner (time-based reminders)
# -----------------------------------------------------
@celery.task(name="backend.tasks.reminders.daily_reminder_runner")
def daily_reminder_runner():
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST)
    print("REMINDERS EXECUTED")

    for u in User.query.filter(User.active == True).all():
        if not u.receive_reminders:
            continue

        hh, mm = map(int, getattr(u, "reminder_time", "18:00").split(":"))

        if now_ist.hour == hh and now_ist.minute == mm:
            if u.last_reminder_sent_at:
                last_ist = u.last_reminder_sent_at.astimezone(IST)
                if last_ist.date() == now_ist.date():
                    continue

            if qualifies_for_reminder(u):
                send_user_reminder(u.id, {"channels": ["email", "gchat"]})
                u.last_reminder_sent_at = now_utc
                db.session.commit()


# -----------------------------------------------------
# Send reminder action
# -----------------------------------------------------
@celery.task(name="backend.tasks.reminders.send_user_reminder")
def send_user_reminder(user_id, action):
    u = User.query.get(user_id)
    if not u:
        return

    msg = build_reminder_message(u)
    channels = action.get("channels", ["gchat"])

    if "gchat" in channels and u.google_chat_webhook:
        send_google_chat(u.google_chat_webhook, msg)

    if "email" in channels:
        send_email(u.email, "Parking Reminder", f"<p>{msg}</p>")
