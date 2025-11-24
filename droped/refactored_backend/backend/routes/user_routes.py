from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, send_file
from flask_restful import Api, Resource
from sqlalchemy import extract, func

from backend.app import db
from backend.models import ParkingLot, ParkingSpot, Reservation, User, dateFormat
from backend.routes.utils.auth import auth_required, current_user
from backend.routes.utils.serialization import serialize_list

# If you already have a global Redis / Celery integration, import from there.
from backend.extensions import redis_conn  # type: ignore


user_bp = Blueprint("user", __name__, url_prefix="/api/user")
api = Api(user_bp)


utcnow = lambda: datetime.now(timezone.utc)


def err(msg, code: int = 400):
    return {"error": msg}, code


class SpotActivityResource(Resource):
    """Single rich resource for user spot operations and reports.

    POST:
        { "action": "book", ... }
        { "action": "release", ... }

    GET:
        /api/user/spots?view=reservations|summary|monthly|location|recent|activity
    """

    method_decorators = [auth_required]

    # ---------- Book / Release Spot ----------

    def post(self):
        data = request.get_json() or {}
        action = data.get("action")

        if action == "book":
            return self._book_spot(data)
        if action == "release":
            return self._release_spot(data)

        return err("Invalid or missing action (book/release)")

    # ---------- Reports / views ----------

    def get(self):
        user = current_user()
        view = request.args.get("view", "reservations")

        if view == "reservations":
            return self._reservations(user)
        if view == "summary":
            return self._summary(user)
        if view == "monthly":
            return self._monthly(user)
        if view == "location":
            return self._location(user)
        if view == "recent":
            return self._recent(user)
        if view == "activity":
            return self._activity(user)

        return err("Unknown view parameter")

    # ---------- Sub-actions ----------

    def _book_spot(self, data):
        user = current_user()
        lot_id = data.get("lot_id")
        vehicle = data.get("vehicle_no")
        driver_name = data.get("driver_name")
        driver_contact = data.get("driver_contact")

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

        reservation = Reservation(
            user_id=user.id,
            spot_id=spot.id,
            vehicle_number=vehicle,
            driver_name=driver_name,
            driver_contact=driver_contact,
            start_time=utcnow(),
        )
        spot.status = "O"
        db.session.add(reservation)
        db.session.commit()

        return {
            "message": "Spot booked",
            "reservation_id": reservation.id,
            "spot_id": spot.id,
        }, 201

    def _release_spot(self, data):
        user = current_user()
        res_id = data.get("reservation_id")
        if not res_id:
            return err("reservation_id is required")

        reservation = db.session.get(Reservation, res_id)
        if not reservation:
            return err("Reservation not found", 404)
        if reservation.user_id != user.id and not user.is_admin:
            return err("Unauthorized", 403)
        if reservation.end_time:
            return err("Already released")

        reservation.end_time = utcnow()
        reservation.spot.status = "A"
        dur_hrs = (
            reservation.end_time - reservation.start_time
        ).total_seconds() / 3600
        reservation.parking_fee = round(dur_hrs * reservation.spot.lot.price, 2)
        db.session.commit()

        return {"message": "Spot released", "cost": reservation.parking_fee}, 200

    # ---------- View helpers ----------

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
            db.session.query(
                func.coalesce(func.sum(Reservation.parking_fee), 0),
            )
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
            "avg_monthly": round(spend / months, 2) if months else 0.0,
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
        months = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
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
                {
                    "location": r[0],
                    "amount": float(r[1] or 0),
                    "count": r[2],
                }
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
                Reservation.user_id == user.id,
                Reservation.start_time >= since,
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


# ---------- List Lots by Pin Code ----------


class LotsResource(Resource):
    method_decorators = [auth_required]

    def get(self):
        pin_code = request.args.get("pin_code")
        if not pin_code:
            return {"error": "pin_code query parameter is required"}, 400

        lots = ParkingLot.query.filter_by(pin_code=pin_code).all()
        return serialize_list(
            lots,
            extra_fn=lambda lot: {
                "number_of_spots": lot.number_of_spots,
                "available_spots": sum(
                    1 for s in lot.spots if s.status == "A"
                ),
            },
        ), 200


# ---------- List Available Pin Codes ----------


class PinCodesResource(Resource):
    method_decorators = [auth_required]

    def get(self):
        pin_codes = db.session.query(ParkingLot.pin_code).distinct().all()
        return [p[0] for p in pin_codes], 200


# ---------- User Profile ----------


class UserProfileResource(Resource):
    method_decorators = [auth_required]

    def get(self, user_id: int):
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "User not found"}, 404
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        }, 200


# ---------- Export CSV via Celery ----------


class ExportCSVResource(Resource):
    method_decorators = [auth_required]

    def post(self):
        user = current_user()
        user_id = user.id

        from backend.tasks.export_tasks import (
            export_user_history_csv,
        )  # local import to avoid cycles

        task = export_user_history_csv.delay(user_id)

        return {
            "message": "Export started",
            "task_id": task.id,
        }, 202


class ExportStatusResource(Resource):
    method_decorators = [auth_required]

    def get(self, task_id: str):
        from celery.result import AsyncResult

        result = AsyncResult(task_id)

        if result.state == "SUCCESS":
            filepath = redis_conn.get(f"task:{task_id}:result")
            if filepath:
                return {
                    "status": "completed",
                    "download_url": f"/api/user/download/{task_id}",
                }

        return {"status": result.state}


class ExportDownloadResource(Resource):
    method_decorators = [auth_required]

    def get(self, task_id: str):
        filepath = redis_conn.get(f"task:{task_id}:result")
        if not filepath:
            return {"error": "File not ready"}, 404

        return send_file(
            filepath.decode(),
            as_attachment=True,
        )


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

# One rich endpoint for spot operations + user reports
api.add_resource(SpotActivityResource, "/spots")

# Discovery helpers
api.add_resource(LotsResource, "/lots")
api.add_resource(PinCodesResource, "/pincodes")

# Profile + exports
api.add_resource(UserProfileResource, "/profile/<int:user_id>")
api.add_resource(ExportCSVResource, "/export-csv")
api.add_resource(ExportStatusResource, "/export-status/<string:task_id>")
api.add_resource(ExportDownloadResource, "/download/<string:task_id>")
