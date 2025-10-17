
from flask_restful import Resource, Api, reqparse
from flask import request ,Blueprint
from sqlalchemy import func, extract
from werkzeug.security import generate_password_hash
from datetime import datetime, UTC, timezone ,timedelta
from backend.app import db
from backend.models import Reservation, ParkingSpot, ParkingLot, User, dateFormat
from backend.routes.utils.auth import auth_required, admin_required, current_user

user_bp = Blueprint("user", __name__, url_prefix="/api/user")
api = Api(user_bp)


# ---------- Book a Spot ----------
class BookSpotResource(Resource):
    method_decorators = [auth_required]  

    def post(self):
        user = current_user()
        data = request.get_json()
        lot_id = data.get("lot_id")
        vehicle_number = data.get("vehicle_no")
        request_user_id = data.get("user_id")
        driver_name = data.get("driver_name")
        driver_contact = data.get("driver_contact")

        if not request_user_id or user.id != int(request_user_id):
            return {"error": "User ID is required"}, 400
        if not lot_id or not vehicle_number:
            return {"error": "lot_id and vehicle_number are required"}, 400

        lot = db.session.get(ParkingLot, lot_id)
        if not lot:
            return {"error": "Invalid parking lot"}, 404

        # first available spot
        spot = ParkingSpot.query.filter_by(lot_id=lot.id, status="A").first()
        if not spot:
            return {"error": "No available spots in this lot"}, 400

        slot_for_car = Reservation.get_slot_for_car(vehicle_number)
        if slot_for_car:
            return {"error": "This vehicle is already parked at " + slot_for_car.label}, 400

        # create reservation 
        reservation = Reservation(
            user_id=user.id,
            spot_id=spot.id,
            vehicle_number=vehicle_number,
            start_time=datetime.now(UTC),
            driver_name=driver_name,
            driver_contact=driver_contact
        )
        spot.status = "O"

        db.session.add(reservation)
        db.session.commit()

        return {
            "message": "Spot booked successfully",
            "reservation_id": reservation.id,
            "lot_id": lot.id,
            "spot_id": spot.id
        }, 201


# ---------- Release a Spot ----------
class ReleaseSpotResource(Resource):
    method_decorators = [auth_required]

    def post(self, res_id):
        user = current_user()
        reservation = db.session.get(Reservation, res_id)

        if not reservation:
            return {"error": "Reservation not found"}, 404
        if reservation.user_id != user.id and not user.is_admin:
            return {"error": "Unauthorized release attempt"}, 403
        if reservation.end_time:
            return {"error": "Spot already released"}, 400

        reservation.end_time = datetime.now(UTC)
        reservation.spot.status = "A"

        # cost
        lot_price = reservation.spot.lot.price
        start = reservation.start_time
        end = reservation.end_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        duration_hours = (end - start).total_seconds() / 3600
        reservation.parking_fee = round(duration_hours * lot_price, 2)

        db.session.commit()

        return {
            "message": "Spot released successfully",
            "reservation_id": res_id,
            "spot_id": reservation.spot_id,
            "lot_id": reservation.spot.lot_id,
            "cost": reservation.parking_fee
        }, 200


# ---------- User Reservations ----------
class UserReservationsResource(Resource):
    method_decorators = [auth_required]

    def get(self):
        user = current_user()
        reservations = Reservation.query.filter_by(user_id=user.id).all()

        result = []
        for r in reservations:
            lot = r.spot.lot if r.spot else None
            result.append({
                "id": r.id,
                "spot_id": r.spot.label if r.spot else None,
                "lot_prefix": lot.prefix if lot else None,
                "vehicle_number": r.vehicle_number,
                "start_time": dateFormat(r.start_time),
                "end_time": dateFormat(r.end_time),
                "driver_name": r.driver_name,
                "driver_contact": r.driver_contact,
                "status": "active" if not r.end_time else "completed",
                "cost": r.parking_fee
            })

        return result, 200


# ---------- List Lots by Pin Code ----------
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


# ---------- List Available Pin Codes ----------
class PinCodesResource(Resource):
    method_decorators = [auth_required]

    def get(self):
        pin_codes = db.session.query(ParkingLot.pin_code).distinct().all()
        return [p[0] for p in pin_codes], 200


# ---------- User Profile ----------
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
            
        }, 200


class UserSummaryResource(Resource):
    method_decorators = [auth_required]
    def get(self):
        try:
            # year from query string, fallback = current year
            year = request.args.get("year", type=int) or datetime.now(timezone.utc).year
            user = current_user()
            user_id = user.id

            # Base query for reservations in that year
            reservations = (
                db.session.query(Reservation)
                .filter(
                    Reservation.user_id == user_id,
                    extract("year", Reservation.start_time) == year
                )
            )
            # total reservations
            total_reservations = reservations.count()

            # total spend (sum of fees, coalesce to 0 if null)
            total_spend = (
                db.session.query(func.coalesce(func.sum(Reservation.parking_fee), 0))
                .filter(
                    Reservation.user_id == user_id,
                    extract("year", Reservation.start_time) == year
                )
                .scalar()
            )

            # average monthly spend (spread across months passed so far)
            months_passed = 12 if year < datetime.now(timezone.utc).year else datetime.now(timezone.utc).month
            avg_monthly = round(total_spend / months_passed, 2) if months_passed else 0


            # active subscriptions (example: reservations without end_time & still active)
            active_subscriptions = (
                db.session.query(Reservation)
                .filter(
                    Reservation.user_id == user_id,
                    Reservation.active == True,
                    Reservation.end_time == None
                )
                .count()
            )


            return {
                "year": year,
                "total_spend": round(total_spend, 2),
                "avg_monthly": avg_monthly,
                "total_reservations": total_reservations,
                "active_subscriptions": active_subscriptions
            }, 200

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500



# -------- Monthly Spend Report --------
class MonthlyReportResource(Resource):
    method_decorators = [auth_required]
    def get(self):
        year = request.args.get("year", type=int) or datetime.now(timezone.utc).year
        user = current_user()
        user_id = user.id

        results = (
            db.session.query(
                extract("month", Reservation.start_time).label("month"),
                func.sum(Reservation.parking_fee).label("amount")
            )
            .filter(
                Reservation.user_id == user_id,
                extract("year", Reservation.start_time) == year
            )
            .group_by("month")
            .all()
        )

        # Build response: months as short names, amounts aligned
        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        amounts = [0] * 12
        for month, amt in results:
            amounts[int(month)-1] = float(amt or 0)

        return {
            "months": months,
            "amounts": amounts
        }, 200


# -------- Location-wise Spend --------
class LocationReportResource(Resource):
    method_decorators = [auth_required]
    def get(self):
        year = request.args.get("year", type=int) or datetime.now(timezone.utc).year
        user = current_user()
        user_id = user.id

        results = (
            db.session.query(
                ParkingLot.name.label("lot_name"),
                func.sum(Reservation.parking_fee).label("amount"),
                func.count(Reservation.id).label("count")
            )
            .join(Reservation.spot)
            .join(ParkingLot)
            .filter(
                Reservation.user_id == user_id,
                extract("year", Reservation.start_time) == year
            )
            .group_by(ParkingLot.name)
            .all()
        )

        locations = [r.lot_name for r in results]
        amounts = [float(r.amount or 0) for r in results]
        top = [
            {"location": r.lot_name, "amount": float(r.amount or 0), "count": r.count}
            for r in results
        ]

        return {
            "locations": locations,
            "amounts": amounts,
            "top": top
        }, 200


# -------- Reservation Activity --------
class ActivityReportResource(Resource):
    method_decorators = [auth_required]
    def get(self):
        months_back = request.args.get("months", type=int) or 6
        user = current_user()
        user_id = user.id

        since = datetime.now(timezone.utc) - timedelta(days=30 * months_back)

        results = (
            db.session.query(
                func.strftime("%Y-%m", Reservation.start_time).label("month"),
                func.count(Reservation.id).label("count")
            )
            .filter(
                Reservation.user_id == user_id,
                Reservation.start_time >= since
            )
            .group_by("month")
            .all()
        )

        months = [r[0] for r in results]
        counts = [r[1] for r in results]

        return {
            "months": months,
            "counts": counts
        }, 200


# -------- Recent Reservations --------
class RecentReservationsResource(Resource):
    method_decorators = [auth_required]
    def get(self):
        user = current_user()
        user_id = user.id

        reservations = (
            db.session.query(Reservation)
            .join(Reservation.spot)
            .join(ParkingLot)
            .filter(Reservation.user_id == user_id)
            .order_by(Reservation.start_time.desc())
            .limit(5)
            .all()
        )

        return [
            {
                "id": r.id,
                "lot_name": r.spot.lot.name if r.spot and r.spot.lot else None,
                "spot_name": r.spot.label if r.spot else None,
                "start_time": r.start_time.isoformat(),
                "parking_fee": r.parking_fee or 0
            }
            for r in reservations
        ], 200


api.add_resource(PinCodesResource, "/pincodes")
api.add_resource(UserReservationsResource, "/reservations")
api.add_resource(LotsResource, "/lots")
api.add_resource(BookSpotResource, "/book")
api.add_resource(ReleaseSpotResource, "/release/<int:res_id>")
api.add_resource(UserProfileResource, "/profile/<int:user_id>")
api.add_resource(UserSummaryResource, "/reports/summary")

api.add_resource(MonthlyReportResource, "/reports/monthly")
api.add_resource(LocationReportResource, "/reports/location")
api.add_resource(ActivityReportResource, "/reports/activity")
api.add_resource(RecentReservationsResource, "/reports/recent")

