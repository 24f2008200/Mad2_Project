# backend/tasks/rules.py
from datetime import datetime, timedelta
from sqlalchemy import func
from zoneinfo import ZoneInfo

from backend.celery_instance import celery


from backend.extensions import db
from backend.models import (
    User, Rule, ParkingLot, Reservation,
    ScheduledJobRun
)

# -----------------------------------------------------
# Predicate Registry
# -----------------------------------------------------
predicate_registry = {}

def predicate(name):
    def deco(fn):
        predicate_registry[name] = fn
        return fn
    return deco


@predicate("not_visited_in_days")
def pred_not_visited(user, cond, dbs):
    days = int(cond.get("days", 7))
    cutoff = datetime.utcnow() - timedelta(days=days)
    if not user.last_login:
        return True
    return user.last_login < cutoff


@predicate("has_booked_in_days")
def pred_booked(user, cond, dbs):
    days = int(cond["days"])
    cutoff = datetime.utcnow() - timedelta(days=days)
    return dbs.query(Reservation).filter(
        Reservation.user_id == user.id,
        Reservation.start_time >= cutoff
    ).count() > 0


# -----------------------------------------------------
# Evaluate rule per user
# -----------------------------------------------------
def evaluate_conditions_for_user(rule, user, dbs):
    for cond in rule.conditions or []:
        fn = predicate_registry.get(cond.get("name"))
        if not fn:
            return False
        if not fn(user, cond, dbs):
            return False
    return True


# -----------------------------------------------------
# Return list of user IDs matching rule
# -----------------------------------------------------
def resolve_users_for_rule(rule, dbs):
    q = dbs.query(User)
    matched = []
    for user in q.all():
        if evaluate_conditions_for_user(rule, user, dbs):
            matched.append(user.id)
    return matched


# -----------------------------------------------------
# Does rule fire right now?
# -----------------------------------------------------
def should_fire_rule_now(rule, now_utc):
    sched = rule.schedule or {}
    typ = sched.get("type", "daily")

    IST = ZoneInfo("Asia/Kolkata")
    now_ist = now_utc.astimezone(IST)

    if typ == "daily":
        t = sched.get("time")
        if t:
            hh, mm = map(int, t.split(":"))
            return now_ist.hour == hh and now_ist.minute == mm
        return True

    elif typ == "monthly":
        day = int(sched.get("day", 1))
        hh, mm = map(int, sched.get("time", "02:00").split(":"))
        return now_ist.day == day and now_ist.hour == hh and now_ist.minute == mm

    return False


# -----------------------------------------------------
# POLLER — runs every minute from Celery beat
# -----------------------------------------------------
@celery.task(name="backend.tasks.rules.poll_rules")
def poll_rules():
    now = datetime.utcnow()
    rules = db.session.query(Rule).filter(Rule.enabled == True).all()
    print("POLL RULES EXECUTED")
    for r in rules:
        if should_fire_rule_now(r, now):
            run = ScheduledJobRun(rule_id=r.id, status="pending", run_time=now)
            db.session.add(run)
            db.session.commit()

            run_rule.delay(r.id, run.id)


# -----------------------------------------------------
# RUN RULE — evaluate rule + trigger actions
# -----------------------------------------------------
@celery.task(name="backend.tasks.rules.run_rule")
def run_rule(rule_id, run_record_id):
    dbs = db.session
    rule = dbs.query(Rule).get(rule_id)
    if not rule:
        return

    users = resolve_users_for_rule(rule, dbs)

    rr = dbs.query(ScheduledJobRun).get(run_record_id)
    if rr:
        rr.status = "running"
        dbs.commit()

    # dispatch actions
    dispatched = 0
    for uid in users:
        for action in rule.actions:
            if action.get("action") == "send_reminder":
                from backend.tasks.reminders import send_user_reminder
                send_user_reminder.delay(uid, action)
                dispatched += 1

    if rr:
        rr.status = "success"
        rr.details = {"matched": len(users), "dispatched": dispatched}
        dbs.commit()
