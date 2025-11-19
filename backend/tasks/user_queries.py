# backend/tasks/user_queries.py
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from backend.app import db
from backend.models import User, ParkingLot, Reservation


def users_to_remind(days_inactive=7):
    """Return users inactive for more than `days_inactive` days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_inactive)
    sub = (
        db.session.query(
            Reservation.user_id,
            func.max(Reservation.created_at).label("last_visit")
        )
        .group_by(Reservation.user_id)
        .subquery()
    )

    q = (
        db.session.query(User)
        .outerjoin(sub, User.id == sub.c.user_id)
        .filter((sub.c.last_visit == None) | (sub.c.last_visit < cutoff))
    )
    return q.all()


def users_with_new_parking_lot(since_days=7):
    """Return all users if a new parking lot was added recently."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    lots = ParkingLot.query.filter(ParkingLot.created_at >= cutoff).all()
    if not lots:
        return []
    return User.query.all()


def build_reminder_message(user):
    """Generate personalized reminder text for a user."""
    return f"Hi {user.name}, we noticed you haven't booked parking recently. If you need a spot tonight, book now!"
