from backend.extensions import db
from backend.models import Reservation, ParkingSpot, ParkingLot
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

class ReservationService:
    @staticmethod
    def book_spot(user, lot_id, vehicle_no, driver_name=None, driver_contact=None):
        lot = ParkingLot.query.get(lot_id)
        if not lot:
            return {"error": "Invalid parking lot"}, 404
        if Reservation.get_slot_for_car(vehicle_no):
            return {"error": "Vehicle already parked"}, 400
        spot = ParkingSpot.query.filter_by(lot_id=lot.id, status="A").first()
        if not spot:
            return {"error": "No available spots"}, 400
        r = Reservation(
            user_id=user.id,
            spot_id=spot.id,
            vehicle_number=vehicle_no,
            driver_name=driver_name,
            driver_contact=driver_contact,
            start_time=utcnow()
        )
        spot.status = "O"
        db.session.add(r)
        db.session.commit()
        return {"message": "Spot booked", "reservation_id": r.id, "spot_id": spot.id}, 201

    @staticmethod
    def release_spot(user, reservation_id):
        r = db.session.get(Reservation, reservation_id)
        if not r:
            return {"error": "Reservation not found"}, 404
        if r.user_id != user.id and not getattr(user, "is_admin", False):
            return {"error": "Unauthorized"}, 403
        if r.end_time:
            return {"error": "Already released"}, 400
        r.end_time = utcnow()
        r.spot.status = "A"
        dur_hrs = (r.end_time - r.start_time).total_seconds() / 3600
        r.parking_fee = round(dur_hrs * r.spot.lot.price, 2)
        db.session.commit()
        return {"message": "Spot released", "cost": r.parking_fee}, 200

reservation_service = ReservationService()
