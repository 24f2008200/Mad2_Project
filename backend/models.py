from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from backend.app import db
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, func

class SerializerMixin:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def to_dict(self):
        """Convert SQLAlchemy model instance into dictionary (safe for JSON)."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

class User(db.Model, SerializerMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(120))
    mobile = db.Column(db.String(20))
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(50), default="user")
    address = db.Column(db.String(512))

    def set_password(self, password: str):
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)


class ParkingLot(db.Model, SerializerMixin):
    __tablename__ = "parking_lot"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    prefix = db.Column(db.String(3), nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    address = db.Column(db.String(512))
    pin_code = db.Column(db.String(20))
    max_slots = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    spots = db.relationship("ParkingSpot", backref="lot", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.prefix and self.name:
            self.prefix = self.name[:3].upper()
        if self.max_slots and not self.spots:
            self.spots = [
                ParkingSpot(lot_id=self.id, label=f"{self.prefix} {i + 1}", status="A")
                for i in range(self.max_slots)
            ]

    @hybrid_property
    def number_of_spots(self):
        return len(self.spots)
    
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
        self.spots.remove(spot)
        db.session.delete(spot)
        db.session.flush()  
        self.max_slots -= 1
    def add_spot(self, label: str = None):
        new_spot_number = len(self.spots) + 1
        new_label = label or f"{self.prefix} {new_spot_number}"
        new_spot = ParkingSpot(lot_id=self.id, label=new_label, status="A")
        self.spots.append(new_spot)
        self.max_slots += 1
        db.session.flush() 


    def resize_spots(self, new_count: int):
        current_count = len(self.spots)

        if new_count > current_count:
            # Add new spots
            for i in range(current_count + 1, new_count + 1):
                self.add_spot(label=f"{self.prefix} {i}")
        elif new_count < current_count:            
            to_remove = [s for s in self.spots if s.status == "A"]
            to_remove = to_remove[: current_count - new_count]
            if len(to_remove) < (current_count - new_count):
                raise ValueError("Not enough available spots to remove")
            for spot in to_remove:
                self.spots.remove(spot)
                db.session.delete(spot)

        self.max_slots = len(self.spots)
        db.session.flush()


class ParkingSpot(db.Model, SerializerMixin):
    __tablename__ = "parking_spot"

    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey("parking_lot.id"), nullable=False)
    status = db.Column(db.String(1), nullable=False, default="A")  # A=available, O=occupied
    label = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reservations = db.relationship("Reservation", back_populates="spot", lazy=True)
    @property
    def occupied(self):
        return self.status == 'O'
    @property
    def current_reservation(self):
        # returns the first active one
        for r in self.reservations:
            if r.end_time is None:
                return r
        return None

    @property
    def current_vehicle_number(self):
        res = self.current_reservation
        return res.vehicle_number if res else None

    @property
    def get_details(self):
        r = self.current_reservation
        u = r.user if r else None
        return {
            "id": self.id,
            "label": self.label,
            "status": self.status,
            "vehicle_number": r.vehicle_number if r else None,
            "occupied_since": r.start_time if r else None,
            "user_name": u.name if u else None,
            "driver_contact": r.driver_contact if r else None,
            "driver_name": r.driver_name if r else None,
            "end_time": r.end_time if r else None
        }

class Reservation(db.Model, SerializerMixin):
    __tablename__ = "reservation"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey("parking_spot.id"), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)   
    driver_contact = db.Column(db.String(20), nullable=True)
    driver_name = db.Column(db.String(120), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    parking_fee = db.Column(db.Float, nullable=True)
    active = db.Column(db.Boolean, default=True)

    # Relationships
    user = db.relationship("User", backref="reservations")
    spot = db.relationship("ParkingSpot", back_populates="reservations")

    # def end_reservation(self, end_time, cost: float):
    #     self.end_time = end_time
    #     self.parking_fee = cost
    #     self.active = False
