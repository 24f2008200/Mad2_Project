from flask_restful import Resource, Api
from flask import request, Blueprint
from sqlalchemy import func, extract
from datetime import datetime, timezone, timedelta
from backend.app import db
from backend.models import Reservation, ParkingSpot, ParkingLot, dateFormat
from backend.routes.utils.auth import auth_required, current_user

user_bp = Blueprint("user", __name__, url_prefix="/api/user")
api = Api(user_bp)

utcnow = lambda: datetime.now(timezone.utc)
err = lambda msg, code=400: ({"error": msg}, code)


class SpotActivityResource(Resource):
    method_decorators = [auth_required]

    # ---------- Book a Spot ----------
    def post(self):
        data = request.get_json() or {}
        action = data.get("action")

        if action == "book":
            return self._book_spot(data)
        elif action == "release":
            return self._release_spot(data)
        return err("Invalid or missing action (book/release)")

    # ---------- Get user’s reservations / reports ----------
    def get(self):
        user = current_user()
        view = request.args.get("view", "reservations")

        if view == "reservations":
            return self._reservations(user)
        elif view == "summary":
            return self._summary(user)
        elif view == "monthly":
            return self._monthly(user)
        elif view == "location":
            return self._location(user)
        elif view == "recent":
            return self._recent(user)
        elif view == "activity":
            return self._activity(user)
        return err("Unknown view parameter")

    # ---------- Sub-actions ----------

    def _book_spot(self, data):
        user = current_user()
        lot_id, vehicle = data.get("lot_id"), data.get("vehicle_no")
        driver_name, driver_contact = data.get("driver_name"), data.get("driver_contact")

        if not lot_id or not vehicle:
            return err("lot_id and vehicle_no are required")

        lot = db.session.get(ParkingLot, lot_id)
        if not lot:
            return err("Invalid parking lot", 404)
        if Reservation.get_slot_for_car(vehicle):
            return err("Vehicle already parked")

        spot = ParkingSpot.query.filter_by(lot_id=lot.id, status="A").first()
        if not spot:
            return err("No available spots")

        r = Reservation(
            user_id=user.id, spot_id=spot.id, vehicle_number=vehicle,
            driver_name=driver_name, driver_contact=driver_contact, start_time=utcnow()
        )
        spot.status = "O"
        db.session.add(r)
        db.session.commit()
        return {"message": "Spot booked", "reservation_id": r.id, "spot_id": spot.id}, 201

    def _release_spot(self, data):
        user = current_user()
        res_id = data.get("reservation_id")
        if not res_id:
            return err("reservation_id is required")

        r = db.session.get(Reservation, res_id)
        if not r:
            return err("Reservation not found", 404)
        if r.user_id != user.id and not user.is_admin:
            return err("Unauthorized", 403)
        if r.end_time:
            return err("Already released")

        r.end_time = utcnow()
        r.spot.status = "A"
        dur_hrs = (r.end_time - r.start_time).total_seconds() / 3600
        r.parking_fee = round(dur_hrs * r.spot.lot.price, 2)
        db.session.commit()
        return {"message": "Spot released", "cost": r.parking_fee}, 200

    def _reservations(self, user):
        reservations = Reservation.query.filter_by(user_id=user.id).all()
        return [
            {
                "id": r.id,
                "lot": r.spot.lot.name if r.spot else None,
                "spot": r.spot.label if r.spot else None,
                "vehicle": r.vehicle_number,
                "start": dateFormat(r.start_time),
                "end": dateFormat(r.end_time),
                "driver": r.driver_name,
                "status": "active" if not r.end_time else "completed",
                "cost": r.parking_fee
            }
            for r in reservations
        ], 200

    def _summary(self, user):
        year = request.args.get("year", type=int) or utcnow().year
        base = Reservation.query.filter(
            Reservation.user_id == user.id,
            extract("year", Reservation.start_time) == year
        )
        total = base.count()
        spend = db.session.query(
            func.coalesce(func.sum(Reservation.parking_fee), 0)
        ).filter(
            Reservation.user_id == user.id,
            extract("year", Reservation.start_time) == year
        ).scalar()
        months = 12 if year < utcnow().year else utcnow().month
        return {
            "year": year,
            "total_spend": round(spend, 2),
            "avg_monthly": round(spend / months, 2),
            "total_reservations": total,
            "active": base.filter(Reservation.end_time.is_(None)).count()
        }, 200

    def _monthly(self, user):
        year = request.args.get("year", type=int) or utcnow().year
        results = (
            db.session.query(
                extract("month", Reservation.start_time), func.sum(Reservation.parking_fee)
            )
            .filter(Reservation.user_id == user.id, extract("year", Reservation.start_time) == year)
            .group_by(extract("month", Reservation.start_time))
            .all()
        )
        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        amounts = [0]*12
        for m,a in results: amounts[int(m)-1] = float(a or 0)
        return {"months": months, "amounts": amounts}, 200

    def _location(self, user):
        year = request.args.get("year", type=int) or utcnow().year
        results = (
            db.session.query(
                ParkingLot.name, func.sum(Reservation.parking_fee), func.count(Reservation.id)
            )
            .join(Reservation.spot).join(ParkingLot)
            .filter(Reservation.user_id == user.id, extract("year", Reservation.start_time) == year)
            .group_by(ParkingLot.name).all()
        )
        return {
            "locations": [r[0] for r in results],
            "amounts": [float(r[1] or 0) for r in results],
            "top": [{"location": r[0], "amount": float(r[1] or 0), "count": r[2]} for r in results]
        }, 200

    def _activity(self, user):
        months = request.args.get("months", type=int) or 6
        since = utcnow() - timedelta(days=30 * months)
        results = (
            db.session.query(
                func.strftime("%Y-%m", Reservation.start_time), func.count(Reservation.id)
            )
            .filter(Reservation.user_id == user.id, Reservation.start_time >= since)
            .group_by(func.strftime("%Y-%m", Reservation.start_time))
            .all()
        )
        return {"months": [r[0] for r in results], "counts": [r[1] for r in results]}, 200

    def _recent(self, user):
        reservations = (
            db.session.query(Reservation)
            .join(Reservation.spot).join(ParkingLot)
            .filter(Reservation.user_id == user.id)
            .order_by(Reservation.start_time.desc()).limit(5).all()
        )
        return [
            {
                "id": r.id,
                "lot": r.spot.lot.name if r.spot and r.spot.lot else None,
                "spot": r.spot.label if r.spot else None,
                "start": r.start_time.isoformat(),
                "fee": r.parking_fee or 0
            }
            for r in reservations
        ], 200


# Register one single endpoint for all spot-related ops
api.add_resource(SpotActivityResource, "/spots")
