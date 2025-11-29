# models.py
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import TypeDecorator

Base = declarative_base()

# Timezones
UTC = timezone.utc
IST = ZoneInfo("Asia/Kolkata")


def utcnow():
    """Return timezone-aware UTC now (use for defaults)."""
    return datetime.now(UTC)


def to_ist(dt: datetime) -> datetime | None:
    """Convert an aware datetime (UTC or other tz) to IST. Returns None for None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # assume naive are UTC (should be rare because we coerce earlier)
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(IST)


def ensure_aware_utc(dt: datetime | None) -> datetime | None:
    """Ensure a datetime is timezone-aware and in UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # assume naive datetimes are UTC — adjust if you prefer otherwise
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class UTCDateTime(TypeDecorator):
    """
    SQLAlchemy TypeDecorator to store/retrieve timezone-aware datetimes as UTC.

    - process_bind_param: when writing to DB, ensure value is UTC-aware (naive -> treated as UTC)
    - process_result_value: when reading from DB, return timezone-aware UTC datetime
    """
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # make sure value is timezone-aware and in UTC
        v = ensure_aware_utc(value)
        # SQLAlchemy expects naive datetimes for some backends; but when using timezone=True
        # many DBAPIs accept aware datetimes. We keep aware datetimes to avoid loss of info.
        return v

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # DB might return naive; treat it as UTC if naive
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class MyModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Use UTCDateTime with timezone awareness; default and onupdate use utcnow()
    created_at = Column(UTCDateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(UTCDateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    def timestamps_as_ist(self) -> dict:
        """Return created_at/updated_at converted to IST (datetime objects)."""
        return {
            "created_at_ist": to_ist(self.created_at),
            "updated_at_ist": to_ist(self.updated_at),
        }

    def to_dict(self, convert_times_to_ist: bool = True) -> dict:
        """
        Example serializer. Convert datetime fields to ISO strings in IST for API responses.
        Extend/override per-model to include model-specific fields.
        """
        base = {
            "id": self.id,
            "active": self.active,
        }
        if convert_times_to_ist:
            ca = to_ist(self.created_at)
            ua = to_ist(self.updated_at)
            base.update(
                {
                    "created_at": ca.isoformat() if ca is not None else None,
                    "updated_at": ua.isoformat() if ua is not None else None,
                }
            )
        else:
            base.update(
                {
                    "created_at": self.created_at.isoformat() if self.created_at is not None else None,
                    "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
                }
            )
        return base


# --- Your domain models (kept fields from your prior model) --- #

class User(MyModel):
    __tablename__ = "user"
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(120))
    mobile = Column(String(20))
    password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default="user")
    address = Column(String(512))
    receive_reminders = Column(Boolean, default=True, nullable=False)
    reminder_time = Column(String(10))
    google_chat_webhook = Column(String(512))
    last_login = Column(UTCDateTime(timezone=True))
    last_reminder_sent_at = Column(UTCDateTime(timezone=True))

    # relationships
    reservations = relationship("Reservation", back_populates="user", cascade="all, delete-orphan")
    reminder_jobs = relationship("ReminderJob", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self, convert_times_to_ist: bool = True):
        d = super().to_dict(convert_times_to_ist=convert_times_to_ist)
        d.update(
            {
                "email": self.email,
                "name": self.name,
                "mobile": self.mobile,
                "is_admin": self.is_admin,
                "is_blocked": self.is_blocked,
                "role": self.role,
                "address": self.address,
                "receive_reminders": self.receive_reminders,
                "reminder_time": self.reminder_time,
                "google_chat_webhook": self.google_chat_webhook,
                "last_login": to_ist(self.last_login).isoformat() if (self.last_login and convert_times_to_ist) else (self.last_login.isoformat() if self.last_login else None),
                "last_reminder_sent_at": to_ist(self.last_reminder_sent_at).isoformat() if (self.last_reminder_sent_at and convert_times_to_ist) else (self.last_reminder_sent_at.isoformat() if self.last_reminder_sent_at else None),
            }
        )
        return d


class ParkingLot(MyModel):
    __tablename__ = "parkinglot"
    name = Column(String(255), nullable=False)
    prefix = Column(String(3))
    price = Column(Float, default=0.0, nullable=False)
    address = Column(String(512))
    pin_code = Column(String(20))
    max_slots = Column(Integer)

    spots = relationship("ParkingSpot", back_populates="lot", cascade="all, delete-orphan")

    def to_dict(self, convert_times_to_ist: bool = True):
        d = super().to_dict(convert_times_to_ist=convert_times_to_ist)
        d.update(
            {
                "name": self.name,
                "prefix": self.prefix,
                "price": self.price,
                "address": self.address,
                "pin_code": self.pin_code,
                "max_slots": self.max_slots,
            }
        )
        return d


class ParkingSpot(MyModel):
    __tablename__ = "parkingspot"
    lot_id = Column(Integer, ForeignKey("parkinglot.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(1), nullable=False, default="A")  # A=available, O=occupied
    label = Column(String(50))
    premium = Column(String(1), default="N")  # N=normal, P=premium, V=vip

    lot = relationship("ParkingLot", back_populates="spots")
    reservations = relationship("Reservation", back_populates="spot", cascade="all, delete-orphan")

    def to_dict(self, convert_times_to_ist: bool = True):
        d = super().to_dict(convert_times_to_ist=convert_times_to_ist)
        d.update(
            {
                "lot_id": self.lot_id,
                "status": self.status,
                "label": self.label,
                "premium": self.premium,
            }
        )
        return d


class Reservation(MyModel):
    __tablename__ = "reservation"
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    spot_id = Column(Integer, ForeignKey("parkingspot.id", ondelete="CASCADE"), nullable=False)
    vehicle_number = Column(String(20), nullable=False)
    driver_contact = Column(String(20))
    driver_name = Column(String(120))
    start_time = Column(UTCDateTime(timezone=True), default=utcnow)
    end_time = Column(UTCDateTime(timezone=True))
    parking_fee = Column(Float)

    user = relationship("User", back_populates="reservations")
    spot = relationship("ParkingSpot", back_populates="reservations")

    def to_dict(self, convert_times_to_ist: bool = True):
        d = super().to_dict(convert_times_to_ist=convert_times_to_ist)
        d.update(
            {
                "user_id": self.user_id,
                "spot_id": self.spot_id,
                "vehicle_number": self.vehicle_number,
                "driver_contact": self.driver_contact,
                "driver_name": self.driver_name,
                "start_time": to_ist(self.start_time).isoformat() if (self.start_time and convert_times_to_ist) else (self.start_time.isoformat() if self.start_time else None),
                "end_time": to_ist(self.end_time).isoformat() if (self.end_time and convert_times_to_ist) else (self.end_time.isoformat() if self.end_time else None),
                "parking_fee": self.parking_fee,
            }
        )
        return d


class ReminderJob(MyModel):
    __tablename__ = "reminderjob"
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    scheduled_at = Column(UTCDateTime(timezone=True), nullable=False)
    status = Column(String(20), default="pending")
    sent_at = Column(UTCDateTime(timezone=True))

    user = relationship("User", back_populates="reminder_jobs")

    def to_dict(self, convert_times_to_ist: bool = True):
        d = super().to_dict(convert_times_to_ist=convert_times_to_ist)
        d.update(
            {
                "user_id": self.user_id,
                "scheduled_at": to_ist(self.scheduled_at).isoformat() if (self.scheduled_at and convert_times_to_ist) else (self.scheduled_at.isoformat() if self.scheduled_at else None),
                "status": self.status,
                "sent_at": to_ist(self.sent_at).isoformat() if (self.sent_at and convert_times_to_ist) else (self.sent_at.isoformat() if self.sent_at else None),
            }
        )
        return d

# Add any indexes or unique constraints you had earlier
# e.g. UniqueConstraint(User.email) is already ensured by unique=True on the column.
