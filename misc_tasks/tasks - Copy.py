# backend/tasks/tasks.py
"""
Celery tasks and rule evaluator backbone.

Usage:
- Configure CELERY_BROKER_URL and CELERY_RESULT_BACKEND env vars.
- Start celery worker: celery -A tasks worker -l info
- Start celery beat (or scheduler): celery -A tasks beat -l info
  but we will schedule poll_rules via beat or system cron; poll_rules has builtin guard to avoid double-run.
"""

import os
from datetime import datetime, timedelta, time as dt_time
from typing import List, Dict, Any, Optional

from celery import  shared_task
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import func, and_, or_

from backend.celery_app import celery
from backend.utils.storage import upload_file_to_s3, presigned_url_for_key, S3_PREFIX
import csv, tempfile, os
# Import your SQLAlchemy objects and helpers
from backend.models import (
    db,           # optional: if you keep engine in models.py
    utcnow,
    to_ist,
    ensure_aware_utc,
    User,
    Reservation,
    ParkingLot,
    ReminderJob,
    Rule,
    ScheduledJobRun,
    ExportJob,
)

# CELERY config - adjust to your environment
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# celery = Celery("parking_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

# Optional configuration: task serialization, retries, etc.
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# DB session factory - prefer importing your app's session. Fallback to engine from models.
SessionLocal = db.session #scoped_session(sessionmaker(bind=db.engine, autoflush=False, autocommit=False))


# -------------------------
# Predicate registry (safe, pluggable)
# -------------------------
predicate_registry = {}


def predicate(name):
    def deco(fn):
        predicate_registry[name] = fn
        return fn
    return deco


@predicate("not_visited_in_days")
def pred_not_visited(user: User, cond: Dict[str, Any], db) -> bool:
    """
    Returns True if user.last_login is older than 'days' or is null.
    cond: {"days": 7}
    """
    days = int(cond.get("days", 7))
    cutoff = utcnow() - timedelta(days=days)
    if not user.last_login:
        return True
    # user.last_login is expected to be UTC-aware
    return user.last_login < cutoff


@predicate("has_booked_in_days")
def pred_has_booked_in_days(user: User, cond: Dict[str, Any], db) -> bool:
    """
    True if user has reservation in last N days.
    cond: {"days":30}
    """
    days = int(cond.get("days", 30))
    cutoff = utcnow() - timedelta(days=days)
    # simple query count
    cnt = db.query(func.count(Reservation.id)).filter(
        Reservation.user_id == user.id,
        Reservation.start_time >= cutoff
    ).scalar()
    return cnt > 0


@predicate("has_parkinglot_created_by_admin_in_days")
def pred_parkinglot_created_by_admin(user: User, cond: Dict[str, Any], db) -> bool:
    """
    Example predicate: Are there parkinglots created by admins within last N days
    cond: {"days":30}
    """
    days = int(cond.get("days", 30))
    cutoff = utcnow() - timedelta(days=days)
    # Assuming ParkingLot has a 'created_at' and a 'created_by' field if you add it.
    # If you don't have created_by, adapt accordingly.
    # Here we check if ANY parkinglot created in window (global condition, not per-user).
    cnt = db.query(func.count(ParkingLot.id)).filter(
        ParkingLot.created_at >= cutoff
    ).scalar()
    return cnt > 0

# --- add these imports near top of tasks.py ---
from sqlalchemy import func, desc
from collections import Counter
from datetime import timedelta

# --- add these predicate implementations to the predicate registry ---

@predicate("spent_more_than")
def pred_spent_more_than(user: User, cond: Dict[str, Any], db) -> bool:
    """
    Returns True if user total spent in a period > amount.
    cond: {"amount": 100.0, "days": 30}  (days optional; if missing, checks all-time)
    """
    amount = float(cond.get("amount", 0))
    days = cond.get("days")
    q = db.query(func.coalesce(func.sum(Reservation.parking_fee), 0)).filter(Reservation.user_id == user.id)
    if days:
        cutoff = utcnow() - timedelta(days=int(days))
        q = q.filter(Reservation.start_time >= cutoff)
    total_spent = q.scalar() or 0.0
    return float(total_spent) > amount


@predicate("most_used_parkinglot_in_period")
def pred_most_used_parkinglot_in_period(user: User, cond: Dict[str, Any], db) -> bool:
    """
    Returns True if the user's most used parking lot in the given window matches a condition (optional).
    cond: {"days":30, "min_count":3}
    If only used as a metric in preview, this predicate can return True if count >= min_count.
    """
    days = int(cond.get("days", 30))
    min_count = int(cond.get("min_count", 1))
    cutoff = utcnow() - timedelta(days=days)

    # join Reservation -> ParkingSpot -> ParkingLot (assuming relationships exist)
    rows = db.query(ParkingLot.id, func.count(Reservation.id).label("cnt")).join(
        ParkingSpot, ParkingSpot.lot_id == ParkingLot.id
    ).join(
        Reservation, Reservation.spot_id == ParkingSpot.id
    ).filter(
        Reservation.user_id == user.id,
        Reservation.start_time >= cutoff
    ).group_by(ParkingLot.id).order_by(desc("cnt")).all()

    if not rows:
        return False
    top_lot_id, top_count = rows[0][0], rows[0][1]
    return top_count >= min_count

# -------------------------
# Helper: evaluate conditions for a given user and rule
# -------------------------
def evaluate_conditions_for_user(rule: Rule, user: User, db) -> bool:
    """
    rule.conditions is expected to be a JSON array of predicate objects.
    Example predicate object:
      {"name":"not_visited_in_days", "days":7}
    All predicates must be true for the user to match (logical AND). You may extend to support OR groups later.
    """
    conds = rule.conditions or []
    for cond in conds:
        name = cond.get("name") or cond.get("type")
        if not name:
            # skip invalid
            continue
        fn = predicate_registry.get(name)
        if fn is None:
            # unknown predicate => treat as false (safe)
            return False
        # Each predicate gets (user, cond, db)
        matched = fn(user, cond, db)
        if not matched:
            return False
    return True


# -------------------------
# Resolve users for rule (small scale, naive approach). For large scale, you must batch.
# -------------------------
def resolve_users_for_rule(rule: Rule, db) -> List[int]:
    """
    Returns list of user ids matching the rule (subject to rule.target).
    Basic implementation: fetch candidate users (all or targeted), then filter using predicate functions.
    """

    # Start with base query: all users
    q = db.query(User)

    # Apply basic targeting if rule.target provided (e.g., specific user ids or parkinglot ids)
    target = rule.target or {}
    if target.get("user_ids"):
        q = q.filter(User.id.in_(target["user_ids"]))
    # Add other target filters here if desired

    # Avoid loading huge user set into memory in one shot; here we iterate in batches.
    matched_user_ids = []
    batch_size = 200
    offset = 0
    while True:
        batch = q.order_by(User.id).limit(batch_size).offset(offset).all()
        if not batch:
            break
        for user in batch:
            try:
                if evaluate_conditions_for_user(rule, user, db):
                    matched_user_ids.append(user.id)
            except Exception:
                # safe: skip user on predicate error
                continue
        offset += batch_size

    return matched_user_ids


# -------------------------
# Scheduling helpers (supports simple daily/monthly/cron)
# -------------------------
def should_fire_rule_now(rule: Rule, now_utc: datetime) -> bool:
    """
    Decide if rule should be fired at this check time.
    Supports schedule types:
      - {"type":"daily","time":"18:00"}  -> fire daily at given local time (assumed IST)
      - {"type":"daily","time_field":"reminder_time","fallback_time":"18:00"} -> per-user time (handled later)
      - {"type":"monthly","day":1,"time":"02:00"} -> fire monthly on day/time (IST)
      - {"type":"cron","expr":"0 18 * * *"} -> cron expression (optional)
    NOTE: For per-user times (time_field), this function returns True to allow run_rule to perform per-user scheduling.
    """
    sched = rule.schedule or {}
    typ = sched.get("type", "daily")

    # Convert now_utc to IST for schedule comparison
    from zoneinfo import ZoneInfo
    IST = ZoneInfo("Asia/Kolkata")
    now_ist = now_utc.astimezone(IST)

    if typ == "daily":
        # if 'time' is present -> global daily at time
        t = sched.get("time")
        if t:
            hh, mm = map(int, t.split(":"))
            return now_ist.hour == hh and now_ist.minute == mm
        # if time_field present -> per-user scheduling; let poller trigger run_rule and run_rule will handle users
        if sched.get("time_field"):
            # run_rule should be scheduled and handle per-user time matching
            # We return True every minute so run_rule will evaluate users' time_field.
            return True

    elif typ == "monthly":
        day = int(sched.get("day", 1))
        t = sched.get("time", "02:00")
        hh, mm = map(int, t.split(":"))
        return now_ist.day == day and now_ist.hour == hh and now_ist.minute == mm

    elif typ == "cron":
        # lightweight cron checker, optional dependency 'croniter' can be used. For safety, we skip cron here.
        expr = sched.get("expr")
        if expr:
            try:
                from croniter import croniter
                prev = croniter(expr, now_ist).get_prev(datetime)
                # crude: if prev is within last minute (i.e., schedule matched now)
                return (now_ist - prev) < timedelta(seconds=70)
            except Exception:
                return False

    return False


# -------------------------
# Celery periodic poller
# -------------------------
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run poll_rules every 60 seconds (you may change to 30s / 300s)
    sender.add_periodic_task(60.0, poll_rules.s(), name="poll_rules_every_minute")


@shared_task(bind=True)
def poll_rules(self):
    """
    Runs periodically (every minute). Fetches active rules and enqueues run_rule for those that should fire.
    """
    db = SessionLocal
    try:
        now = utcnow()
        rules = db.query(Rule).filter(Rule.enabled == True).all()
        for r in rules:
            try:
                if should_fire_rule_now(r, now):
                    # create a ScheduledJobRun record to track execution
                    run = ScheduledJobRun(rule_id=r.id, status="pending", run_time=now)
                    db.add(run); db.commit()
                    # enqueue rule execution
                    run_rule.delay(r.id, run.id)
            except Exception as e:
                # log and continue
                db.rollback()
                continue
    finally:
        db.close()


# -------------------------
# run_rule: evaluate rule and dispatch actions
# -------------------------
@shared_task(bind=True, max_retries=3)
def run_rule(self, rule_id: int, run_record_id: Optional[int] = None):
    """
    Evaluate the rule, resolve matching users (using predicates), and enqueue actions.
    """
    db = SessionLocal
    try:
        rule = db.query(Rule).get(rule_id)
        if rule is None:
            return

        # mark running
        run_rec = None
        if run_record_id:
            run_rec = db.query(ScheduledJobRun).get(run_record_id)
            if run_rec:
                run_rec.status = "running"
                db.commit()

        # Resolve users
        matched_user_ids = resolve_users_for_rule(rule, db)

        # For rules where schedule.time_field exists (per-user reminder_time), filter users to those whose
        # user.reminder_time equals the current IST minute.
        schedule = rule.schedule or {}
        if schedule.get("type") == "daily" and schedule.get("time_field"):
            time_field = schedule.get("time_field")  # e.g. "reminder_time"
            # Build final list by checking user's time field equals current IST time (HH:MM)
            from zoneinfo import ZoneInfo
            IST = ZoneInfo("Asia/Kolkata")
            now_ist = utcnow().astimezone(IST)
            now_hm = f"{now_ist.hour:02d}:{now_ist.minute:02d}"
            filtered = []
            for uid in matched_user_ids:
                u = db.query(User).get(uid)
                user_time = getattr(u, time_field, None)
                if user_time is None:
                    user_time = schedule.get("fallback_time")  # e.g. "18:00"
                if user_time == now_hm:
                    filtered.append(uid)
            matched_user_ids = filtered

        # Dispatch actions (could be batched)
        dispatched = 0
        for uid in matched_user_ids:
            for action in rule.actions:
                action_name = action.get("action")
                if action_name == "send_reminder":
                    # action may include channels e.g. {"action":"send_reminder","channels":["gchat","email"]}
                    send_reminder.delay(uid, action, rule.id)
                    dispatched += 1
                elif action_name == "generate_and_email_report":
                    # generate monthly report for this user (async)
                    # we pass action to instruct channels or parameters
                    generate_monthly_report.delay(uid, action, rule.id)
                    dispatched += 1
                # add more action types as needed

        # update run record
        if run_rec:
            run_rec.status = "success"
            run_rec.details = {"matched": len(matched_user_ids), "dispatched": dispatched}
            db.commit()
    except Exception as exc:
        db.rollback()
        if run_record_id:
            rr = db.query(ScheduledJobRun).get(run_record_id)
            if rr:
                rr.status = "failed"
                rr.details = {"error": str(exc)}
                db.commit()
        raise
    finally:
        db.close()


# -------------------------
# Action: send_reminder (worker)
# -------------------------
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_reminder(self, user_id: int, action: Dict[str, Any], rule_id: Optional[int] = None):
    """
    Sends reminder to a user via configured channels.
    action example: {"action":"send_reminder","channels":["gchat","email"], "template":"reminder_v1"}
    """
    db = SessionLocal
    try:
        user: User = db.query(User).get(user_id)
        if not user:
            return

        channels = action.get("channels", ["gchat"])
        template_name = action.get("template", "default_reminder")

        # Render message (simple format; replace with Jinja2 as needed)
        msg = f"Hello {user.name or user.email},\nThis is your parking reminder."

        # GChat
        if "gchat" in channels:
            webhook = user.google_chat_webhook
            if webhook:
                try:
                    import requests
                    payload = {"text": msg}
                    requests.post(webhook, json=payload, timeout=10)
                except Exception:
                    # don't fail whole task; just log
                    pass

        # Email: placeholder - integrate with your mail sender
        if "email" in channels:
            try:
                # send_email(user.email, subject="Parking reminder", html=msg)  # implement send_email in your codebase
                pass
            except Exception:
                pass

        # Record reminder job
        r = ReminderJob(user_id=user.id, scheduled_at=utcnow(), status="sent", sent_at=utcnow())
        db.add(r)
        # update user.last_reminder_sent_at
        user.last_reminder_sent_at = utcnow()
        db.commit()
    except Exception as exc:
        db.rollback()
        raise
    finally:
        db.close()


# -------------------------
# Action: generate_monthly_report (worker)
# -------------------------
@shared_task(bind=True)
def generate_monthly_report(self, user_id: int, action: Dict[str, Any], rule_id: Optional[int] = None):
    """
    Generate an HTML monthly report for the user and email it.
    Placeholder: implement template & email integration.
    """
    db = SessionLocal
    try:
        user = db.query(User).get(user_id)
        if not user:
            return

        # Find last month window (example: previous calendar month)
        now = utcnow()
        first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = first_of_this_month - timedelta(seconds=1)
        last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Query reservations in month
        rows = db.query(Reservation).filter(
            Reservation.user_id == user.id,
            Reservation.start_time >= last_month_start,
            Reservation.start_time <= last_month_end
        ).all()

        # Compute simple metrics
        total_bookings = len(rows)
        total_spent = sum((r.parking_fee or 0) for r in rows)
        # most used parking lot
        lot_counts = {}
        for r in rows:
            try:
                lot = r.spot.lot  # relationship available
                lot_counts[lot.name] = lot_counts.get(lot.name, 0) + 1
            except Exception:
                continue
        most_used = max(lot_counts.items(), key=lambda x: x[1])[0] if lot_counts else None

        # Render HTML - you should replace with Jinja2 template rendering
        html = f"""
        <h1>Monthly Parking Report</h1>
        <p>User: {user.name or user.email}</p>
        <p>Period: {last_month_start.date()} to {last_month_end.date()}</p>
        <ul>
          <li>Total bookings: {total_bookings}</li>
          <li>Total spent: {total_spent}</li>
          <li>Most used lot: {most_used}</li>
        </ul>
        """

        # TODO: save html to storage and send as attachment via email
        # send_email(user.email, subject="Your monthly parking report", html=html)

    finally:
        db.close()


# -------------------------
# Action: export_user_csv (user-triggered job)
# -------------------------
@shared_task(bind=True)
def export_user_csv(self, export_job_id: int):
    """
    Worker that creates CSV for ExportJob.params and updates ExportJob.result_url
    """
    db = SessionLocal
    try:
        job: ExportJob = db.query(ExportJob).get(export_job_id)
        if not job:
            return
        job.status = "running"
        db.commit()

        # Example: params = {"from":"2024-01-01","to":"2024-10-31"}
        params = job.params or {}
        from_s = params.get("from")
        to_s = params.get("to")
        if from_s:
            from_dt = ensure_aware_utc(datetime.fromisoformat(from_s))
        else:
            from_dt = None
        if to_s:
            to_dt = ensure_aware_utc(datetime.fromisoformat(to_s))
        else:
            to_dt = utcnow()

        # Query reservations for user between window
        q = db.query(Reservation).filter(Reservation.user_id == job.user_id)
        if from_dt:
            q = q.filter(Reservation.start_time >= from_dt)
        if to_dt:
            q = q.filter(Reservation.start_time <= to_dt)

        rows = q.order_by(Reservation.start_time).all()

        # Write CSV to local file (or S3)
        import csv, tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        with open(tmp.name, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            # header
            writer.writerow(["reservation_id", "spot_id", "start_time_utc", "end_time_utc", "parking_fee", "vehicle_number"])
            for r in rows:
                writer.writerow([
                    r.id,
                    r.spot_id,
                    r.start_time.isoformat() if r.start_time else "",
                    r.end_time.isoformat() if r.end_time else "",
                    r.parking_fee or "",
                    r.vehicle_number or "",
                ])
         # Write CSV to local temporary file
        
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        tmpname = tmp.name
        tmp.close()
        with open(tmpname, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["reservation_id", "spot_id", "start_time_utc", "end_time_utc", "parking_fee", "vehicle_number"])
            for r in rows:
                writer.writerow([
                    r.id,
                    r.spot_id,
                    r.start_time.isoformat() if r.start_time else "",
                    r.end_time.isoformat() if r.end_time else "",
                    r.parking_fee or "",
                    r.vehicle_number or "",
                ])

        # Upload to S3
        import uuid
        file_key = f"{S3_PREFIX.rstrip('/')}/{job.user_id}/export_{job.id}_{uuid.uuid4().hex}.csv"
        upload_file_to_s3(tmpname, file_key)

        # Generate presigned URL (e.g., 24 hours)
        url = presigned_url_for_key(file_key, expires_in=86400)
        job.result_url = url
        job.status = "done"
        db.commit()

        # cleanup local file
        try:
            os.remove(tmpname)
        except Exception:
            pass
        # TODO: upload tmp.name to S3 and set URL
        # For now, set local path as result_url (not ideal for multi-worker / prod)
        job.result_url = f"file://{tmp.name}"
        job.status = "done"
        db.commit()

        # Notify user via email / gchat
        # notify_user_export_ready(job.user_id, job.result_url)

    except Exception as exc:
        db.rollback()
        if job:
            job.status = "failed"
            job.error = str(exc)
            db.commit()
        raise
    finally:
        db.close()


@celery.task
def test_add(x, y):
    print("Task running...", x, y)
    return x + y
