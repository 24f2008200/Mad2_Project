
from flask import request, send_file, Blueprint
from flask_restful import Resource, Api
from sqlalchemy import func, extract
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
from io import BytesIO
import base64
from datetime import datetime, timezone
from collections import defaultdict

from backend.extensions import db, cache
from backend.models import (
    ParkingLot,
    ParkingSpot,
    Reservation,
    User,
    dateFormat,
    search_all,
    ReminderJob,
    model_to_dict
)
from backend.routes.utils.auth import admin_required
from backend.services.parking_service import get_all_lots

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
api = Api(admin_bp)


def serialize_list(queryset):
    return [model_to_dict(obj) for obj in queryset]


class LotsResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        # cached list of lots (service returns json-serializable data)
        cache_key = "all_lots"
        cached = cache.get(cache_key)
        if cached:
            return cached, 200
        data = get_all_lots()
        cache.set(cache_key, data, timeout=120)
        return data, 200

    def post(self):
        data = request.get_json() or {}
        lot = ParkingLot(
            name=data["name"],
            prefix=data.get("prefix"),
            price=data["price"],
            address=data.get("address"),
            pin_code=data.get("pin_code"),
            max_slots=data.get("number_of_spots", 0),
            created_at=func.now(),
        )
        db.session.add(lot)
        db.session.commit()
        cache.delete("all_lots")
        return {"message": "Parking lot created", "id": lot.id}, 201


class LotResource(Resource):
    method_decorators = [admin_required]

    def put(self, lot_id):
        lot = ParkingLot.query.get_or_404(lot_id)
        data = request.get_json() or {}
        try:
            if "number_of_spots" in data:
                lot.resize_spots(data["number_of_spots"])
        except ValueError as e:
            return {"error": str(e)}, 400
        lot.name = data.get("name", lot.name)
        lot.price = data.get("price", lot.price)
        lot.address = data.get("address", lot.address)
        lot.pin_code = data.get("pin_code", lot.pin_code)
        db.session.commit()
        cache.delete("all_lots")
        # Invalidate some report caches that depend on lot structure
        cache.delete("admin_report_occupancy")
        cache.delete("admin_report_revenue")
        cache.delete("admin_report_summary")
        return {"message": "Parking lot updated"}, 200

    def delete(self, lot_id):
        lot = db.session.get(ParkingLot, lot_id)
        if not lot:
            return {"error": "Lot not found"}, 404
        if ParkingSpot.query.filter_by(lot_id=lot.id, status="O").count() > 0:
            return {"error": "Cannot delete lot with active spots"}, 400
        db.session.delete(lot)
        db.session.commit()
        cache.delete("all_lots")
        cache.delete("admin_report_occupancy")
        cache.delete("admin_report_revenue")
        cache.delete("admin_report_summary")
        return {"message": "Lot deleted"}, 200


class SlotResource(Resource):
    method_decorators = [admin_required]

    def delete(self, slot_id):
        slot = ParkingSpot.query.get_or_404(int(slot_id))
        if slot.status == "O":
            return {"error": "Cannot delete occupied slot"}, 400
        lot = slot.lot
        lot.delete_spot(slot.id)
        db.session.commit()
        cache.delete("all_lots")
        cache.delete("admin_report_occupancy")
        cache.delete("admin_report_revenue")
        cache.delete("admin_report_summary")
        return {"message": "Parking slot deleted"}, 200


class SearchResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        search_type = request.args.get("type")
        search_by = request.args.get("search_by", "").strip()
        value = request.args.get("value", "").strip()

        if not search_type:
            return {"error": "Missing ?type= parameter"}, 400

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
            return serialize_list(query.all()), 200

        elif search_type == "bookings":
            query = Reservation.query.join(User)
            if search_by == "name":
                query = query.filter(User.name.ilike(f"%{value}%"))
            elif search_by == "mobile":
                query = query.filter(User.mobile.ilike(f"%{value}%"))
            elif search_by == "address":
                query = query.filter(User.address.ilike(f"%{value}%"))
            elif search_by == "vehicle_number":
                query = query.filter(Reservation.vehicle_number.ilike(f"%{value}%"))
            elif search_by == "driver":
                query = query.filter(Reservation.driver_name.ilike(f"%{value}%"))
            elif search_by == "parking_lot":
                query = (
                    query.join(ParkingSpot)
                    .join(ParkingLot)
                    .filter(ParkingLot.name.ilike(f"%{value}%"))
                )

            return [r.get_details for r in query.all()], 200

        elif search_type == "lots":
            return get_all_lots(), 200

        elif search_type == "bquery":
            results = search_all(value)
            return results, 200

        else:
            return {"error": f"Unsupported search type: {search_type}"}, 400


class AdminReportResource(Resource):
    method_decorators = [admin_required]

    def post(self):
        data = request.get_json() or {}
        opCode = data.get("opCode", "summary")
        print("Admin report view requested:", opCode)
        if opCode == "summary":
            return self._summary()
        if opCode == "occupancy":
            return self._occupancy()
        if opCode == "revenue":
            return self._revenue()
        if opCode == "reservations_by_lot":
            return self._reservations_by_lot()
        if opCode == "reservation":
            return self._reservations(data)
        if opCode == "user":
            return self._users(data)
        if opCode == "reminder":
            return self._reminder_logs(data)

        return {"error": f"Unsupported view: {opCode}"}, 400

    def _summary(self):
        key = "admin_report_summary"
        cached = cache.get(key)
        if cached:
            return cached, 200

        total_users = User.query.count()
        active_reservations = Reservation.query.filter(Reservation.end_time.is_(None)).count()
        lots = ParkingLot.query.count()

        revenue = (
            db.session.query(
                func.strftime("%Y-%m", Reservation.start_time).label("month"),
                func.sum(Reservation.parking_fee).label("total"),
            )
            .group_by("month")
            .all()
        )

        revenue_data = [{"month": r[0], "amount": float(r[1] or 0)} for r in revenue]

        result = {
            "total_users": total_users,
            "active_reservations": active_reservations,
            "lots": lots,
            "revenue": revenue_data,
        }

        cache.set(key, result, timeout=120)
        return result, 200

    def _occupancy(self):
        key = "admin_report_occupancy"
        cached = cache.get(key)
        if cached:
            return cached, 200

        lots = ParkingLot.query.all()
        data = []
        for lot in lots:
            occupied = lot.occupied_spots
            available = lot.number_of_spots - occupied
            data.append({"lot": lot.name, "available": available, "occupied": occupied})

        cache.set(key, data, timeout=120)
        return data, 200

    def _revenue(self):
        key = "admin_report_revenue"
        cached = cache.get(key)
        if cached:
            return cached, 200

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

        for lot, month, revenue in results:
            m = int(month)
            months_seen.add(m)
            data[lot][m] = float(revenue or 0)

        if months_seen:
            min_month, max_month = min(months_seen), max(months_seen)
        else:
            cache.set(key, {"range": {"start": 1, "end": 0}, "data": {}}, timeout=120)
            return {"range": {"start": 1, "end": 0}, "data": {}}, 200

        final_data = {}
        for lot, month_dict in data.items():
            final_data[lot] = {m: month_dict.get(m, 0.0) for m in range(min_month, max_month + 1)}

        result = {"range": {"start": min_month, "end": max_month}, "data": final_data}
        cache.set(key, result, timeout=120)
        print("Revenue report data:", result)
        return result, 200

    def _reservations_by_lot(self):
        key = "admin_report_reservations_by_lot"
        cached = cache.get(key)
        if cached:
            return cached, 200

        results = (
            db.session.query(
                ParkingLot.name, func.count(Reservation.id).label("bookings")
            )
            .join(Reservation.spot)
            .join(ParkingLot)
            .group_by(ParkingLot.name)
            .all()
        )
        data = [{"lot": lot, "bookings": bookings} for lot, bookings in results]
        cache.set(key, data, timeout=120)
        return data, 200

    def _reservations(self, data):
        query = Reservation.query
        user_id = data.get("user_id")
        if user_id:
            query = query.filter(Reservation.user_id == int(user_id))

        lot_id = data.get("lot_id")
        if lot_id:
            query = query.join(Reservation.spot).filter(ParkingSpot.lot_id == int(lot_id))

        if data.get("active_only"):
            query = query.filter(Reservation.end_time.is_(None))
        
        start_date = data.get("startDate")
        if start_date:
            dt_start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            query = query.filter(Reservation.start_time >= dt_start)

        return [r.get_details for r in query.all()], 200

    def _users(self, data):
        query = User.query
        email = data.get("email")
        if email:
            query = query.filter(User.email.ilike(f"%{email}%"))

        mobile = data.get("mobile")
        if mobile:
            query = query.filter(User.mobile.ilike(f"%{mobile}%"))

        rr = data.get("receive_reminders")
        if isinstance(rr, bool):
            query = query.filter(User.receive_reminders == rr)

        return serialize_list(query.all()), 200

    def _reminder_logs(self, data):
        page = int(data.get("page", 1))
        per_page = int(data.get("per_page", 20))

        status = data.get("status")
        user_id = data.get("user_id")
        date_from = data.get("date_from")
        date_to = data.get("date_to")

        query = ReminderJob.query

        if status:
            query = query.filter(ReminderJob.status == status)

        if user_id:
            query = query.filter(ReminderJob.user_id == int(user_id))

        if date_from:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            query = query.filter(ReminderJob.scheduled_at >= dt_from)

        if date_to:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(tzinfo=timezone.utc)
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
                    "sent_at": job.sent_at.isoformat() if job.sent_at else None,
                    "error_message": getattr(job, "error_message", None),
                    "created_at": job.created_at.isoformat(),
                }
            )

        if not logs:
            logs = [
                {
                    "id": "12",
                    "user_id": "34",
                    "user_name": "test user",
                    "scheduled_at": datetime.now(timezone.utc).date().isoformat(),
                    "status": "sent",
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "error_message": "None",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "id": "13",
                    "user_id": "35",
                    "user_name": "another user",
                    "scheduled_at": datetime.now(timezone.utc).date().isoformat(),
                    "status": "sent",
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "error_message": "None",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            ]
        return logs, 200
        # return {
        #     "page": page_obj.page,
        #     "pages": page_obj.pages,
        #     "total": page_obj.total,
        #     "items": logs,
        # }, 200


class PdfReportResource(Resource):
    method_decorators = [admin_required]

    def post(self):
        data = request.get_json() or {}
        charts = data.get("charts", [])

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "Parking Lot Monthly Report")

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

        p.showPage()
        y = height - 100
        for chart in charts:
            try:
                img_data = chart["data"].split(",")[1]
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
            except Exception as e:
                print("Error embedding chart:", e)

        p.save()
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name="Parking_Report.pdf",
            mimetype="application/pdf",
        )


api.add_resource(LotsResource, "/lots")
api.add_resource(LotResource, "/lots/<int:lot_id>")
api.add_resource(SlotResource, "/slots/<int:slot_id>")
api.add_resource(SearchResource, "/search")
api.add_resource(AdminReportResource, "/reports")
api.add_resource(PdfReportResource, "/reports/pdf")
