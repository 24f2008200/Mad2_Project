
from flask_restful import Resource, Api
from flask import request, Blueprint
from sqlalchemy import func, extract
from datetime import datetime, timezone, timedelta
from backend.app import db
from backend.models import Reservation, ParkingSpot, ParkingLot, dateFormat, User
from backend.routes.utils.auth import auth_required, current_user

user_bp = Blueprint("user", __name__, url_prefix="/api/user")
api = Api(user_bp)

utcnow = lambda: datetime.now(timezone.utc)
err = lambda msg, code=400: ({"error": msg}, code)


class SpotActivityResource(Resource):
    method_decorators = [auth_required]

    def post(self):
        data = request.get_json() or {}
        action = data.get("action")

        if action == "book":
            return self._book_spot(data)
        elif action == "release":
            return self._release_spot(data)
        return err("Invalid or missing action (book/release)")

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
            user_id=user.id,
            spot_id=spot.id,
            vehicle_number=vehicle,
            driver_name=driver_name,
            driver_contact=driver_contact,
            start_time=utcnow(),
        )
        spot.status = "O"
        db.session.add(r)
        db.session.commit()
        # Invalidate cached admin lists & reports that depend on occupancy
        from backend.extensions import cache
        cache.delete("all_lots")
        cache.delete("admin_report_occupancy")
        cache.delete("admin_report_summary")
        cache.delete("admin_report_revenue")
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

        if r.start_time.tzinfo is None:
            r.start_time = r.start_time.replace(tzinfo=timezone.utc)
        if r.end_time.tzinfo is None:
            r.end_time = r.end_time.replace(tzinfo=timezone.utc)
            
        print(r.start_time, r.end_time)
        dur_hrs = (r.end_time - r.start_time).total_seconds() / 3600
        r.parking_fee = round(dur_hrs * r.spot.lot.price, 2)
        db.session.commit()
        from backend.extensions import cache
        cache.delete("all_lots")
        cache.delete("admin_report_occupancy")
        cache.delete("admin_report_summary")
        cache.delete("admin_report_revenue")
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
                "cost": r.parking_fee,
            }
            for r in reservations
        ], 200

    def _summary(self, user):
        year = request.args.get("year", type=int) or utcnow().year
        base = Reservation.query.filter(
            Reservation.user_id == user.id,
            extract("year", Reservation.start_time) == year,
        )
        total = base.count()
        spend = (
            db.session.query(func.coalesce(func.sum(Reservation.parking_fee), 0))
            .filter(
                Reservation.user_id == user.id,
                extract("year", Reservation.start_time) == year,
            )
            .scalar()
        )
        months = 12 if year < utcnow().year else utcnow().month
        return {
            "year": year,
            "total_spend": round(spend, 2),
            "avg_monthly": round(spend / months, 2),
            "total_reservations": total,
            "active": base.filter(Reservation.end_time.is_(None)).count(),
        }, 200

    def _monthly(self, user):
        year = request.args.get("year", type=int) or utcnow().year
        results = (
            db.session.query(
                extract("month", Reservation.start_time),
                func.sum(Reservation.parking_fee),
            )
            .filter(
                Reservation.user_id == user.id,
                extract("year", Reservation.start_time) == year,
            )
            .group_by(extract("month", Reservation.start_time))
            .all()
        )
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        amounts = [0] * 12
        for m, a in results:
            amounts[int(m) - 1] = float(a or 0)
        return {"months": months, "amounts": amounts}, 200

    def _location(self, user):
        year = request.args.get("year", type=int) or utcnow().year
        results = (
            db.session.query(
                ParkingLot.name,
                func.sum(Reservation.parking_fee),
                func.count(Reservation.id),
            )
            .join(Reservation.spot)
            .join(ParkingLot)
            .filter(
                Reservation.user_id == user.id,
                extract("year", Reservation.start_time) == year,
            )
            .group_by(ParkingLot.name)
            .all()
        )
        return {
            "locations": [r[0] for r in results],
            "amounts": [float(r[1] or 0) for r in results],
            "top": [
                {"location": r[0], "amount": float(r[1] or 0), "count": r[2]}
                for r in results
            ],
        }, 200

    def _activity(self, user):
        months = request.args.get("months", type=int) or 6
        since = utcnow() - timedelta(days=30 * months)
        results = (
            db.session.query(
                func.strftime("%Y-%m", Reservation.start_time),
                func.count(Reservation.id),
            )
            .filter(
                Reservation.user_id == user.id, Reservation.start_time >= since
            )
            .group_by(func.strftime("%Y-%m", Reservation.start_time))
            .all()
        )
        return {
            "months": [r[0] for r in results],
            "counts": [r[1] for r in results],
        }, 200

    def _recent(self, user):
        reservations = (
            db.session.query(Reservation)
            .join(Reservation.spot)
            .join(ParkingLot)
            .filter(Reservation.user_id == user.id)
            .order_by(Reservation.start_time.desc())
            .limit(5)
            .all()
        )
        return [
            {
                "id": r.id,
                "lot": r.spot.lot.name if r.spot and r.spot.lot else None,
                "spot": r.spot.label if r.spot else None,
                "start": r.start_time.isoformat(),
                "fee": r.parking_fee or 0,
            }
            for r in reservations
        ], 200


class LotsResource(Resource):
    method_decorators = [auth_required]

    def get(self):
        pin_code = request.args.get("pin_code")
        if not pin_code:
            return {"error": "pin_code query parameter is required"}, 400

        lots = ParkingLot.query.filter_by(pin_code=pin_code).all()
        return [
            {
                "id": lot.id,
                "name": lot.name,
                "address": lot.address,
                "pin_code": lot.pin_code,
                "price": lot.price,
                "number_of_spots": lot.number_of_spots,
                "available_spots": sum(1 for s in lot.spots if s.status == "A"),
            }
            for lot in lots
        ], 200


class PinCodesResource(Resource):
    method_decorators = [auth_required]

    def get(self):
        pin_codes = db.session.query(ParkingLot.pin_code).distinct().all()
        return [p[0] for p in pin_codes], 200
 

class UserProfileResource(Resource):
    method_decorators = [auth_required]

    def get(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "User not found"}, 404
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mobile": user.mobile,
            "address": user.address,
            "receive_reminders": user.receive_reminders,
            "reminder_time": user.reminder_time,
            "google_chat_webhook": user.google_chat_webhook,
            "total_reservations": user.total_reservations,
            "active_reservations": user.active_reservations,
            "last_login": dateFormat(user.last_login),
            "billing": user.billing,
            "last_active": dateFormat(user.last_active),

        }, 200
    def put(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "User not found"}, 404

        data = request.get_json() or {}
        print(data)
        user.name = data.get("name", user.name)
        user.email = data.get("email", user.email)
        user.mobile = data.get("mobile", user.mobile)
        user.address = data.get("address", user.address)
        user.receive_reminders = data.get("receive_reminders", user.receive_reminders)
        user.reminder_time = data.get("reminder_time", user.reminder_time)
        user.google_chat_webhook = data.get("google_chat_webhook", user.google_chat_webhook)

        password = data.get("password")
        confirm_password = data.get("confirm_password")
        if password:
            if password != confirm_password:
                return {"error": "Passwords do not match"}, 400
            user.set_password(password)

        db.session.commit()
        return {"message": "Profile updated"}, 200

 
class UserReservationsResource(Resource):
    method_decorators = [auth_required]

    def post(self):
        user = current_user()
        data = request.get_json() or {}
        reservations = Reservation.query.filter_by(user_id=user.id).all()
        for r in reservations:
            if r.start_time.tzinfo is None:
                r.start_time = r.start_time.replace(tzinfo=timezone.utc)
        start_date = data.get("startDate")
        if start_date:
            dt_start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            reservations = [r for r in reservations if r.start_time >= dt_start]
        end_date = data.get("endDate")
        if end_date:
            dt_end = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)+ timedelta(days=1)
            reservations = [r for r in reservations if r.start_time <= dt_end]

        result = []
        for r in reservations:
            lot = r.spot.lot if r.spot else None
            result.append(
                {
                    "id": r.id,
                    "spot_id": r.spot.label if r.spot else None,
                    "lot_prefix": lot.prefix if lot else None,
                    "vehicle_number": r.vehicle_number,
                    "start_time": dateFormat(r.start_time),
                    "end_time": dateFormat(r.end_time),
                    "driver_name": r.driver_name,
                    "driver_contact": r.driver_contact,
                    "status": "active" if not r.end_time else "completed",
                    "cost": r.parking_fee,
                }
            )

        return result, 200


api.add_resource(UserProfileResource, "/profile/<int:user_id>")
api.add_resource(SpotActivityResource, "/spots")
api.add_resource(LotsResource, "/lots")
api.add_resource(PinCodesResource, "/pincodes")
api.add_resource(UserReservationsResource, "/reservations")
