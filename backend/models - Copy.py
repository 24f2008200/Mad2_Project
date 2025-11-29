
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from backend.app import db
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, func, inspect, text, event
from sqlalchemy.exc import SQLAlchemyError


class MyModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    active = db.Column(db.Boolean, default=True)

    __serialize_extras__ = []

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def to_dict(self):
        from backend.models import dateFormat  # local import to avoid circular
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if "time" in column.name.lower() and isinstance(value, datetime):
                result[column.name] = dateFormat(value)
            else:
                result[column.name] = value

        extras = getattr(self, "__serialize_extras__", [])
        for name in extras:
            try:
                value = getattr(self, name)
            except AttributeError:
                continue
            if isinstance(value, datetime):
                result[name] = dateFormat(value)
            else:
                result[name] = value

        return result

 
class User(MyModel):
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(120))
    mobile = db.Column(db.String(20))
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(50), default="user")
    address = db.Column(db.String(512))
    receive_reminders = db.Column(db.Boolean, default=True)
    reminder_time = db.Column(db.String(10))
    google_chat_webhook = db.Column(db.String(512))
    last_login = db.Column(db.DateTime, nullable=True)
    last_reminder_sent_at = db.Column(db.DateTime, nullable=True)

    reservations = db.relationship("Reservation", back_populates="user")

    __serialize_extras__ = ["billing", "last_active"]

    def set_password(self, password: str):
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)
    @hybrid_property
    def total_reservations(self):
        return len(self.reservations) if self.reservations else 0
    @hybrid_property
    def active_reservations(self):
        return len([r for r in self.reservations if r.end_time is None]) if self.reservations else 0
    @hybrid_property
    def billing(self):
        return sum(
            [r.parking_fee for r in self.reservations if r.parking_fee is not None]
        )

    @hybrid_property
    def last_active(self):
        last = None
        for r in self.reservations:
            if not last or (r.start_time and r.start_time > last):
                last = r.start_time
            if r.end_time and (not last or r.end_time > last):
                last = r.end_time
        return last


class ParkingLot(MyModel):
    name = db.Column(db.String(255), nullable=False)
    prefix = db.Column(db.String(3), nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    address = db.Column(db.String(512))
    pin_code = db.Column(db.String(20))
    max_slots = db.Column(db.Integer, nullable=True)

    spots = db.relationship(
        "ParkingSpot", backref="lot", cascade="all, delete-orphan"
    )

    __serialize_extras__ = ["occupied_spots", "number_of_spots", "billing"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.prefix and self.name:
            self.prefix = self.name[:3].upper()

    @hybrid_property
    def occupied_spots(self):
        return len([s for s in self.spots if s.status == "O"])

    @hybrid_property
    def number_of_spots(self):
        return len(self.spots)

    @hybrid_property
    def billing(self):
        total = 0.0
        for spot in self.spots:
            total += spot.billing
        return total

    @number_of_spots.expression
    def number_of_spots(cls):
        return (
            select(func.count(ParkingSpot.id))
            .where(ParkingSpot.lot_id == cls.id)
            .correlate(cls)
            .scalar_subquery()
        )

    def delete_spot(self, spot_id):
        spot = next((s for s in self.spots if s.id == spot_id), None)
        if not spot:
            raise ValueError(f"Spot {spot_id} does not exist in lot {self.name}")
        if spot.status == "O":
            raise ValueError(f"Cannot delete spot {spot_id} because it is occupied")
        reservations = Reservation.query.filter_by(spot_id=spot.id).all()
        for res in reservations:
            db.session.delete(res)
        self.spots.remove(spot)
        db.session.delete(spot)
        db.session.flush()
        self.max_slots = len(self.spots)

    def add_spot(self, label: str = None):
        new_spot_number = len(self.spots) + 1
        new_label = label or f"{self.prefix} {new_spot_number}"
        new_spot = ParkingSpot(lot_id=self.id, label=new_label, status="A")
        self.spots.append(new_spot)
        self.max_slots = len(self.spots)
        db.session.flush()

    def resize_spots(self, new_count: int):
        current_count = len(self.spots)
        if new_count > current_count:
            for i in range(current_count + 1, new_count + 1):
                self.add_spot(label=f"{self.prefix} {i}")
        elif new_count < current_count:
            to_remove = [s for s in self.spots if s.status == "A"]
            to_remove = to_remove[: current_count - new_count]
            if len(to_remove) < (current_count - new_count):
                raise ValueError("Not enough available spots to remove")
            for spot in to_remove:
                self.delete_spot(spot.id)
        self.max_slots = len(self.spots)
        db.session.flush()

@event.listens_for(ParkingLot, "after_insert")
def create_spots(mapper, connection, lot):

    if not lot.max_slots:
        return

    spots_table = ParkingSpot.__table__

    # Bulk insert spots in one DB call
    connection.execute(
        spots_table.insert(),
        [
            {
                "lot_id": lot.id,
                "label": f"{lot.prefix} {i+1}",
                "status": "A",
            }
            for i in range(lot.max_slots)
        ]
    )


class ParkingSpot(MyModel):
    lot_id = db.Column(db.Integer, db.ForeignKey("parkinglot.id"), nullable=False)
    status = db.Column(db.String(1), nullable=False, default="A")  # A=available, O=occupied
    label = db.Column(db.String(50))
    premium = db.Column(db.String(1), default="N")  # N=normal, P=premium V=vip

    reservations = db.relationship("Reservation", back_populates="spot", lazy=True)

    __serialize_extras__ = ["billing", "current_vehicle_number"]

    @property
    def occupied(self):
        return self.status == "O"

    @property
    def current_reservation(self):
        for r in self.reservations:
            if r.end_time is None:
                return r
        return None

    @hybrid_property
    def billing(self):
        total = 0.0
        for res in self.reservations:
            if res.parking_fee:
                total += res.parking_fee
        return total

    @property
    def current_vehicle_number(self):
        res = self.current_reservation
        return res.vehicle_number if res else None

    @property
    def get_details(self):
        rs = (
            Reservation.query.filter_by(spot_id=self.id)
            .order_by(Reservation.end_time.desc())
            .all()
        )
        sum_fee = sum(r.parking_fee for r in rs if r.parking_fee)
        r = self.current_reservation
        u = r.user if r else None
        if self.status == "O":
            return {
                "id": self.id,
                "label": self.label,
                "status": self.status,
                "vehicle_number": r.vehicle_number if r else None,
                "occupied_since": dateFormat(r.start_time) if r else None,
                "user_name": u.name if u else None,
                "driver_contact": r.driver_contact if r else None,
                "driver_name": r.driver_name if r else None,
                "end_time": dateFormat(r.end_time) if r else None,
                "total_earnings": sum_fee if sum_fee > 0 else None,
            }
        else:
            r = rs[0] if rs else None
            return {
                "id": self.id,
                "label": self.label,
                "status": self.status,
                "vehicle_number": r.vehicle_number if r else None,
                "occupied_since": dateFormat(r.start_time) if r else None,
                "user_name": r.user.name if r and r.user else None,
                "driver_contact": r.driver_contact if r else None,
                "driver_name": r.driver_name if r else None,
                "end_time": dateFormat(r.end_time) if r else None,
                "total_earnings": sum_fee if sum_fee > 0 else None,
            }


class Reservation(MyModel):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey("parkingspot.id"), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    driver_contact = db.Column(db.String(20), nullable=True)
    driver_name = db.Column(db.String(120), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    parking_fee = db.Column(db.Float, nullable=True)

    user = db.relationship("User", back_populates="reservations")
    spot = db.relationship("ParkingSpot", back_populates="reservations")

    def to_dict(self):
        base = model_to_dict(self)
        base.update(
            {
                "lot_name": self.spot.lot.name if self.spot and self.spot.lot else None,
                "spot_label": self.spot.label if self.spot else None,
                "user_name": self.user.name if self.user else None,
            }
        )
        return base

    @staticmethod
    def get_slot_for_car(vehicle_number):
        return (
            db.session.query(ParkingSpot)
            .join(Reservation)
            .filter(
                Reservation.vehicle_number == vehicle_number,
                Reservation.end_time.is_(None),
            )
            .first()
        )

    @hybrid_property
    def get_details(self):
        return {
            "id": self.id,
            "label": self.spot.label,
            "vehicle_number": self.vehicle_number,
            "start_time": dateFormat(self.start_time),
            "user_name": self.user.name,
            "driver_contact": self.driver_contact,
            "driver_name": self.driver_name,
            "end_time": dateFormat(self.end_time),
            "total_earnings": self.parking_fee,
        }


class ReminderJob(MyModel):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="pending")
    sent_at = db.Column(db.DateTime, nullable=True)


def model_to_dict(obj):
    result = {}
    for col in obj.__table__.columns:
        col_name = col.name
        value = getattr(obj, col_name)

        if col_name.lower() == "password":   #  hide password
            result[col_name] = ""
            continue

        if isinstance(value, datetime):
            result[col_name] = value.strftime("%Y-%m-%d %H:%M:%S")
        else:
            result[col_name] = value

    return result


def model_to_dict_hybrid(obj):
    result = {}

    # 1. Serialize regular columns
    for col in obj.__table__.columns:
        value = getattr(obj, col.name)
        
        if col.name.lower() == "password":   #  hide password
            result[col.name] = ""
            continue

        if isinstance(value, datetime):
            result[col.name] = value.strftime("%Y-%m-%d %H:%M:%S")
        else:
            result[col.name] = value

    # 2. Serialize hybrid properties & extra fields
    extras = getattr(obj, "__serialize_extras__", [])
    for name in extras:
        try:
            value = getattr(obj, name)

            # handle datetime from hybrid property
            if isinstance(value, datetime):
                result[name] = value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                result[name] = value

        except Exception as e:
            result[name] = None  # optional fallback

    return result
def dateFormat(value):
    return value.strftime("%Y-%m-%d %H:%M") if value else None


def search_all(search_term):
    results = []
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    with db.engine.connect() as conn:
        for table in tables:
            columns = [col["name"] for col in inspector.get_columns(table)]
            for col in columns:
                try:
                    query = text(
                            f"""
                            SELECT rowid as id, {col} as value
                            FROM {table}
                            WHERE CAST({col} AS TEXT) LIKE :term
                            """
                        )
                    rows = conn.execute(query, {"term": f"%{search_term}%"}).fetchall()
                    for row in rows:
                        results.append(
                            {
                                "table": table,
                                "column": col,
                                "row_id": row.id,
                                "matched_value": row.value,
                            }
                        )
                except SQLAlchemyError:
                    continue
    return results
