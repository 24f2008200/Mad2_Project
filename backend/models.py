from datetime import datetime,timezone
from werkzeug.security import generate_password_hash, check_password_hash
from backend.app import db
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, func ,inspect, text
from sqlalchemy.exc import SQLAlchemyError

class MyModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone = True), default= lambda : datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone = True), default= lambda : datetime.now(timezone.utc),onupdate= lambda : datetime.now(timezone.utc))
    active = db.Column(db.Boolean, default=True)
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def to_dict(self):
        """Convert SQLAlchemy model instance into dictionary (safe for JSON)."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)

            if "time" in column.name.lower() and isinstance(value, datetime):
                result[column.name] = dateFormat(value)
            else:
                result[column.name] = value

        return result



class User(MyModel):
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(120))
    mobile = db.Column(db.String(20))
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(50), default="user")  # NEW
    address = db.Column(db.String(512))
    receive_reminders = db.Column(db.Boolean, default=True)
    reminder_time = db.Column(db.String(10))

    reservations = db.relationship("Reservation", back_populates="user")

    def set_password(self, password: str):
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)
    @hybrid_property
    def billing(self):
        return sum( [ r.parking_fee for r in self.reservations if r.parking_fee != None] )


class ParkingLot(MyModel):
    name = db.Column(db.String(255), nullable=False)
    prefix = db.Column(db.String(3), nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    address = db.Column(db.String(512))
    pin_code = db.Column(db.String(20))
    max_slots = db.Column(db.Integer, nullable=True)


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
    def occupied_spots(self):
        return len([s for s in self.spots if s.status == "O"])
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

        if new_count > current_count:            # Add new spots
            for i in range(current_count + 1, new_count + 1):
                self.add_spot(label=f"{self.prefix} {i}")
        elif new_count < current_count:            # Remove extra spots (only if they are not reserved)
            to_remove = [s for s in self.spots if s.status == "A"]
            to_remove = to_remove[: current_count - new_count]
            if len(to_remove) < (current_count - new_count):
                raise ValueError("Not enough available spots to remove")
            for spot in to_remove:
                self.spots.remove(spot)
                db.session.delete(spot)

        self.max_slots = len(self.spots)
        db.session.flush()


class ParkingSpot(MyModel):
    lot_id = db.Column(db.Integer, db.ForeignKey("parkinglot.id"), nullable=False)
    status = db.Column(db.String(1), nullable=False, default="A")  # A=available, O=occupied
    label = db.Column(db.String(50))
    reservations = db.relationship("Reservation", back_populates="spot", lazy=True)
    @property
    def occupied(self):
        return self.status == 'O'
    @property
    def current_reservation(self):        # returns the first active one
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
        rs = Reservation.query.filter_by(spot_id=self.id).order_by(Reservation.end_time.desc()).all()
        sum_fee = sum(r.parking_fee for r in rs if r.parking_fee)
        r = self.current_reservation
        u = r.user if r else None
        if self.status == "O":
            return {
                "id": self.id,
                "label": self.label,
                "status": self.status,
                "vehicle_number": r.vehicle_number if r else None,
                "start_time": dateFormat(r.start_time) if r else None,
                "user_name": u.name if u else None,
                "driver_contact": r.driver_contact if r else None,
                "driver_name": r.driver_name if r else None,
                "end_time": dateFormat(r.end_time) if r else None,
                "total_earnings": sum_fee if sum_fee > 0 else None
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
                "total_earnings": sum_fee if sum_fee > 0 else None
        }

class Reservation(MyModel):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey("parkingspot.id"), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)   # NEW
    driver_contact = db.Column(db.String(20), nullable=True)  # NEW
    driver_name = db.Column(db.String(120), nullable=True)  # NEW
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    parking_fee = db.Column(db.Float, nullable=True)


    # Relationships
    user = db.relationship("User", back_populates="reservations")
    spot = db.relationship("ParkingSpot", back_populates="reservations")
    
    def to_dict(self):
        return model_to_dict(self)
    
    def get_slot_for_car(vehicle_number):
        return db.session.query(ParkingSpot).join(Reservation).filter(
            Reservation.vehicle_number == vehicle_number,
            Reservation.end_time == None
        ).first()
     
    @hybrid_property
    def get_details(self):

        return {
                "id": self.id,
                "label": self.spot.label,
             
                "vehicle_number": self.vehicle_number ,
                "start_time": dateFormat(self.start_time) ,
                "user_name": self.user.name ,
                "driver_contact": self.driver_contact ,
                "driver_name": self.driver_name ,
                "end_time": dateFormat(self.end_time) ,
                "total_earnings": self.parking_fee
        }

    # def end_reservation(self, end_time, cost: float): 
    #     self.end_time = end_time
    #     self.parking_fee = cost
    #     self.active = False


def model_to_dict(obj):
    result = {}
    for col in obj.__table__.columns:
        value = getattr(obj, col.name)
        if isinstance(value, datetime):
            result[col.name] = value.strftime("%Y-%m-%d %H:%M:%S") # safe for Vue inputs
        else:
            result[col.name] = value
    return result

def dateFormat(value):
    return value.strftime("%Y-%m-%d %H:%M") if value else None


def search_all(search_term):
    """
    Search across all tables and text-convertible columns in the SQLAlchemy db.
    Returns a list of dicts with table, column, row_id, and matched_value.
    """

    results = []
    inspector = inspect(db.engine)

    # Get all table names
    tables = inspector.get_table_names()

    with db.engine.connect() as conn:
        for table in tables:            # Get all column names
            columns = [col["name"] for col in inspector.get_columns(table)]

            for col in columns:
                try:
                    query = text(f"""
                        SELECT rowid as id, {col} as value
                        FROM {table}
                        WHERE CAST({col} AS TEXT) LIKE :term
                    """)

                    rows = conn.execute(query, {"term": f"%{search_term}%"}).fetchall()

                    for row in rows:
                        results.append({
                            "table": table,
                            "column": col,
                            "row_id": row.id,
                            "matched_value": row.value
                        })
                except SQLAlchemyError:
                    print("Error")
                    # Skip columns that can't be searched
                    continue

    return results
