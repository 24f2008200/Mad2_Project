from collections import defaultdict
from datetime import datetime, timezone

import base64
from io import BytesIO

from flask import Blueprint, request, send_file
from flask_restful import Api, Resource
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from sqlalchemy import extract, func

from backend.extensions import cache, db
from backend.models import (
    ParkingLot,
    ParkingSpot,
    ReminderJob,
    Reservation,
    User,
    dateFormat,
    search_all,
)
from backend.routes.utils.auth import admin_required
from backend.routes.utils.serialization import serialize_list
from backend.services.parking_service import get_all_lots


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
api = Api(admin_bp)


# ---------------------------------------------------------------------------
# Parking Lots
# ---------------------------------------------------------------------------


class LotsResource(Resource):
    method_decorators = [admin_required]

    @cache.cached(timeout=120, key_prefix="all_lots")
    def get(self):
        """Return all lots with aggregated information.

        This uses the parking_service helper which already returns JSON-ready data.
        """
        return get_all_lots(), 200

    def post(self):
        """Create a new parking lot.

        Body:
            name (str)
            price (float)
            prefix (optional, str)
            address (optional, str)
            pin_code (optional, str)
            number_of_spots (optional, int)
        """
        data = request.get_json() or {}

        lot = ParkingLot(
            name=data["name"],
            prefix=data.get("prefix"),
            price=data["price"],
            address=data.get("address"),
            pin_code=data.get("pin_code"),
            max_slots=data.get("number_of_spots", 0),
        )
        db.session.add(lot)
        db.session.commit()
        cache.delete("all_lots")

        return {"message": "Parking lot created", "id": lot.id}, 201


class LotResource(Resource):
    method_decorators = [admin_required]

    def put(self, lot_id: int):
        """Update lot details and resize spots if needed."""
        lot = ParkingLot.query.get_or_404(lot_id)
        data = request.get_json() or {}

        try:
            if "number_of_spots" in data:
                lot.resize_spots(int(data["number_of_spots"]))
        except ValueError as e:
            return {"error": str(e)}, 400

        lot.name = data.get("name", lot.name)
        lot.price = data.get("price", lot.price)
        lot.address = data.get("address", lot.address)
        lot.pin_code = data.get("pin_code", lot.pin_code)

        db.session.commit()
        cache.delete("all_lots")
        return {"message": "Parking lot updated"}, 200

    def delete(self, lot_id: int):
        """Delete a lot (only if no occupied spots)."""
        lot = db.session.get(ParkingLot, lot_id)
        if not lot:
            return {"error": "Lot not found"}, 404

        if ParkingSpot.query.filter_by(lot_id=lot.id, status="O").count() > 0:
            return {"error": "Cannot delete lot with active spots"}, 400

        db.session.delete(lot)
        db.session.commit()
        cache.delete("all_lots")
        return {"message": "Lot deleted"}, 200


class SlotResource(Resource):
    method_decorators = [admin_required]

    def delete(self, slot_id: int):
        """Delete a single slot (only if not occupied)."""
        slot = ParkingSpot.query.get_or_404(int(slot_id))
        if slot.status == "O":
            return {"error": "Cannot delete occupied slot"}, 400

        lot = slot.lot
        lot.delete_spot(slot.id)

        db.session.commit()
        cache.delete("all_lots")
        return {"message": "Parking slot deleted"}, 200


# ---------------------------------------------------------------------------
# Users and Reservations
# ---------------------------------------------------------------------------


class UsersResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        """List all users.

        Uses model.to_dict() and attaches a few computed fields instead of
        manually building the full structure.
        """
        users = User.query.all()
        return serialize_list(
            users,
            extra_fn=lambda u: {
                "rev": getattr(u, "billing", None),
                "last_login": dateFormat(u.last_login),
                # retain original semantics if is_admin is treated as int elsewhere
                "is_blocked": bool(getattr(u, "is_blocked", True)) ,
            },
        ), 200


class ReservationsResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        """List all reservations in a normalized way."""
        reservations = Reservation.query.all()
        return serialize_list(
            reservations,
            extra_fn=lambda r: {
                "lot_id": r.spot.lot_id if r.spot else None,
            },
        ), 200


# ---------------------------------------------------------------------------
# Dashboard summary & reports
# ---------------------------------------------------------------------------


class SummaryResource(Resource):
    method_decorators = [admin_required]

    @cache.cached(timeout=180, key_prefix="summary_data")
    def get(self):
        """High-level dashboard summary."""
        total_users = User.query.count()
        active_reservations = Reservation.query.filter(
            Reservation.end_time.is_(None)
        ).count()
        lots_count = ParkingLot.query.count()

        # simple monthly revenue series (YYYY-MM -> sum)
        revenue = (
            db.session.query(
                func.strftime("%Y-%m", Reservation.start_time).label("month"),
                func.sum(Reservation.parking_fee).label("total"),
            )
            .group_by("month")
            .all()
        )

        revenue_data = [
            {"month": row[0], "amount": float(row[1] or 0)} for row in revenue
        ]

        return {
            "total_users": total_users,
            "active_reservations": active_reservations,
            "lots": lots_count,
            "revenue": revenue_data,
        }, 200


class ReportsResource(Resource):
    """Consolidated reporting endpoint.

    GET /api/admin/reports?type=occupancy|revenue|bookings
    """

    method_decorators = [admin_required]

    @cache.cached(timeout=120, query_string=True)
    def get(self):
        report_type = request.args.get("type", "occupancy")

        if report_type == "occupancy":
            return self._occupancy_report()
        if report_type == "revenue":
            return self._revenue_report()
        if report_type == "bookings":
            return self._booking_report()

        return {"error": f"Unsupported report type: {report_type}"}, 400

    def _occupancy_report(self):
        lots = ParkingLot.query.all()
        data = []
        for lot in lots:
            occupied = lot.occupied_spots
            available = lot.number_of_spots - occupied
            data.append(
                {
                    "lot": lot.name,
                    "available": available,
                    "occupied": occupied,
                }
            )
        return data, 200

    def _revenue_report(self):
        """Revenue by lot and month (compact format)."""
        results = (
            db.session.query(
                ParkingLot.name,
                extract("month", Reservation.start_time).label("month"),
                func.sum(Reservation.parking_fee).label("revenue"),
            )
            .join(Reservation.spot)
            .join(ParkingLot)
            .group_by(ParkingLot.name, "month")
            .all()
        )

        data = defaultdict(dict)
        months_seen = set()

        # Collect raw data
        for lot, month, revenue in results:
            m = int(month)
            months_seen.add(m)
            data[lot][m] = float(revenue or 0)

        # Determine active range
        if not months_seen:
            return {
                "range": {"start": 1, "end": 0},
                "data": {},
            }, 200

        min_month, max_month = min(months_seen), max(months_seen)

        # Fill missing months with 0
        final_data = {}
        for lot, month_dict in data.items():
            final_data[lot] = {
                m: month_dict.get(m, 0.0)
                for m in range(min_month, max_month + 1)
            }

        return {
            "range": {"start": min_month, "end": max_month},
            "data": final_data,
        }, 200

    def _booking_report(self):
        results = (
            db.session.query(
                ParkingLot.name,
                func.count(Reservation.id).label("bookings"),
            )
            .join(Reservation.spot)
            .join(ParkingLot)
            .group_by(ParkingLot.name)
            .all()
        )
        return [
            {"lot": lot, "bookings": bookings} for lot, bookings in results
        ], 200


class PdfReportResource(Resource):
    method_decorators = [admin_required]

    def post(self):
        """Generate PDF with tables + charts.

        Accepts JSON:
            {
                "charts": [
                    { "data": "data:image/png;base64,..." },
                    ...
                ]
            }
        """
        data = request.get_json() or {}
        charts = data.get("charts", [])

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Page 1: Title + Tables
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "Parking Lot Monthly Report")

        # Occupancy summary
        lots = ParkingLot.query.all()
        occupancy_data = [["Lot", "Available Spots", "Occupied Spots"]]
        for lot in lots:
            occupied = lot.occupied_spots
            available = lot.number_of_spots - occupied
            occupancy_data.append([lot.name, available, occupied])

        table = Table(occupancy_data, colWidths=[150, 150, 150])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        table.wrapOn(p, width, height)
        table.drawOn(p, 50, height - 200)

        # Revenue summary
        results = (
            db.session.query(
                ParkingLot.name,
                func.sum(Reservation.parking_fee).label("total_revenue"),
            )
            .join(Reservation.spot)
            .join(ParkingLot)
            .group_by(ParkingLot.name)
            .all()
        )
        revenue_data = [["Lot", "Total Revenue"]]
        for lot, rev in results:
            revenue_data.append([lot, float(rev or 0)])

        table2 = Table(revenue_data, colWidths=[200, 200])
        table2.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        table2.wrapOn(p, width, height)
        table2.drawOn(p, 50, height - 400)

        # Charts
        p.showPage()
        y = height - 100
        for chart in charts:
            try:
                img_data = chart["data"].split(",", 1)[1]
                img_bytes = base64.b64decode(img_data)
                img_buf = BytesIO(img_bytes)
                img_reader = ImageReader(img_buf)
                p.drawImage(
                    img_reader,
                    50,
                    y - 250,
                    width=500,
                    height=250,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                y -= 300
                if y < 200:
                    p.showPage()
                    y = height - 100
            except Exception as exc:  # pragma: no cover - log only
                print("Error embedding chart:", exc)

        p.save()
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name="Parking_Report.pdf",
            mimetype="application/pdf",
        )


# ---------------------------------------------------------------------------
# Search / broad query
# ---------------------------------------------------------------------------


class SearchResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        search_type = request.args.get("type")
        search_by = (request.args.get("search_by") or "").strip()
        value = (request.args.get("value") or "").strip()

        if not search_type:
            return {"error": "Missing ?type= parameter"}, 400

        # -------- USERS --------
        if search_type == "users":
            query = User.query
            if search_by == "name":
                query = query.filter(User.name.ilike(f"%{value}%"))
            elif search_by == "mobile":
                query = query.filter(User.mobile.ilike(f"%{value}%"))
            elif search_by == "email":
                query = query.filter(User.email.ilike(f"%{value}%"))
            elif search_by == "address":
                query = query.filter(User.address.ilike(f"%{value}%"))
            elif search_by == "vehicle":
                query = query.join(Reservation).filter(
                    Reservation.vehicle_number.ilike(f"%{value}%")
                )
            elif search_by == "driver":
                query = query.join(Reservation).filter(
                    Reservation.driver_name.ilike(f"%{value}%")
                )
            elif search_by == "parking_lot":
                query = (
                    query.join(Reservation)
                    .join(ParkingSpot)
                    .join(ParkingLot)
                    .filter(ParkingLot.name.ilike(f"%{value}%"))
                )
            return [u.to_dict() for u in query.all()], 200

        # -------- BOOKINGS --------
        if search_type == "bookings":
            query = Reservation.query.join(User)
            if search_by == "name":
                query = query.filter(User.name.ilike(f"%{value}%"))
            elif search_by == "mobile":
                query = query.filter(User.mobile.ilike(f"%{value}%"))
            elif search_by == "address":
                query = query.filter(User.address.ilike(f"%{value}%"))
            elif search_by == "vehicle_number":
                query = query.filter(
                    Reservation.vehicle_number.ilike(f"%{value}%")
                )
            elif search_by == "driver":
                query = query.filter(
                    Reservation.driver_name.ilike(f"%{value}%")
                )
            elif search_by == "parking_lot":
                query = (
                    query.join(ParkingSpot)
                    .join(ParkingLot)
                    .filter(ParkingLot.name.ilike(f"%{value}%"))
                )

            return [r.get_details for r in query.all()], 200

        # -------- LOTS --------
        if search_type == "lots":
            # Reuse existing service
            return get_all_lots(), 200

        # -------- BROAD QUERY (bquery) --------
        if search_type == "bquery":
            results = search_all(value)
            return results, 200

        return {"error": f"Unsupported search type: {search_type}"}, 400


# ---------------------------------------------------------------------------
# Reminder logs
# ---------------------------------------------------------------------------


class ReminderLogsResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        """Paginated reminder job logs for admins.

        Query params:
            page, per_page
            status (pending/sent/skipped/error)
            user_id
            date_from, date_to (YYYY-MM-DD)
        """
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))

        status = request.args.get("status")
        user_id = request.args.get("user_id")
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")

        query = ReminderJob.query

        if status:
            query = query.filter(ReminderJob.status == status)

        if user_id:
            query = query.filter(ReminderJob.user_id == int(user_id))

        if date_from:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            query = query.filter(ReminderJob.scheduled_at >= dt_from)

        if date_to:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            query = query.filter(ReminderJob.scheduled_at <= dt_to)

        query = query.order_by(ReminderJob.scheduled_at.desc())

        page_obj = query.paginate(page=page, per_page=per_page, error_out=False)

        logs = []
        for job in page_obj.items:
            u = User.query.get(job.user_id)
            logs.append(
                {
                    "id": job.id,
                    "user_id": job.user_id,
                    "user_name": u.name if u else None,
                    "scheduled_at": job.scheduled_at.isoformat(),
                    "status": job.status,
                    "sent_at": job.sent_at.isoformat()
                    if job.sent_at
                    else None,
                    "error_message": getattr(job, "error_message", None),
                    "created_at": job.created_at.isoformat()
                    if job.created_at
                    else None,
                }
            )

        # Keep the sample response as a fallback when DB is empty (useful for UI
        # during early development).
        if not logs:
            now = datetime.now(timezone.utc)
            logs = [
                {
                    "id": "sample-1",
                    "user_id": "1",
                    "user_name": "test user",
                    "scheduled_at": now.date().isoformat(),
                    "status": "sent",
                    "sent_at": now.isoformat(),
                    "error_message": None,
                    "created_at": now.isoformat(),
                },
                {
                    "id": "sample-2",
                    "user_id": "2",
                    "user_name": "another user",
                    "scheduled_at": now.date().isoformat(),
                    "status": "sent",
                    "sent_at": now.isoformat(),
                    "error_message": None,
                    "created_at": now.isoformat(),
                },
            ]

        return logs, 200


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

api.add_resource(LotsResource, "/lots")
api.add_resource(LotResource, "/lots/<int:lot_id>")
api.add_resource(SlotResource, "/slots/<int:slot_id>")
api.add_resource(UsersResource, "/users")
api.add_resource(ReservationsResource, "/reservations")
api.add_resource(SummaryResource, "/summary")
api.add_resource(SearchResource, "/search")

# Consolidated reports
api.add_resource(ReportsResource, "/reports")
api.add_resource(PdfReportResource, "/reports/pdf")
api.add_resource(ReminderLogsResource, "/reminders/logs")
