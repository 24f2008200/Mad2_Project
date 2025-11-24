from flask import request, send_file , Blueprint
from flask_restful import Resource, Api
from sqlalchemy import func, extract
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
from io import BytesIO
import base64
from datetime import datetime,timezone

from backend.extensions import db, cache
from backend.models import ParkingLot, ParkingSpot, Reservation, User, dateFormat, search_all, ReminderJob
from backend.routes.utils.auth import admin_required
from backend.services.parking_service import get_all_lots
from collections import defaultdict


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
api = Api(admin_bp)


# -------- Parking Lot Resources --------
class LotsResource(Resource):
    method_decorators = [admin_required]

    @cache.cached(timeout=120, key_prefix="all_lots")
    def get(self):
        return  get_all_lots(), 200
    
    def post(self):#   Create new parking lot
        data = request.json
        lot = ParkingLot(
            name=data["name"],
            prefix=data.get("prefix"),
            price=data["price"],
            address=data.get("address"),
            pin_code=data.get("pin_code"),
            max_slots=data.get("number_of_spots", 0),
            created_at=func.now()
        )
        db.session.add(lot)
        db.session.commit()
        cache.delete("all_lots")

        return {"message": "Parking lot created", "id": lot.id}, 201


class LotResource(Resource):
    method_decorators = [admin_required]

    def put(self, lot_id):
        """Update lot"""
        lot = ParkingLot.query.get_or_404(lot_id)
        data = request.get_json()
        try:
            lot.resize_spots(data.get("number_of_spots", lot.number_of_spots))
        except ValueError as e:
            return {"error": str(e)}, 400

        lot.name = data.get("name", lot.name)
        lot.price = data.get("price", lot.price)
        lot.address = data.get("address", lot.address)
        lot.pin_code = data.get("pin_code", lot.pin_code)
        db.session.commit()
        cache.delete("all_lots")
        return {"message": "Parking lot updated"}, 200

    def delete(self, lot_id):
        """Delete lot"""
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

    def delete(self, slot_id):
        print(slot_id)

        slot = ParkingSpot.query.get_or_404(int(slot_id))
        if slot.status == "O":
            return {"error": "Cannot delete occupied slot"}, 400
        lot = slot.lot
        lot.delete_spot(slot.id)
        db.session.commit()
        cache.delete("all_lots")
        return {"message": "Parking slot deleted"}, 200


# -------- User & Reservation Resources --------
class UsersResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        """List all users"""
        users = User.query.all()
        return [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "mobile": u.mobile,
                "address": u.address,
                "rev": u.billing,
                "last_login": dateFormat(u.last_login),
                "is_blocked": u.is_admin < 0
            }
            for u in users
        ]
 

class ReservationsResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        """List all reservations"""
        reservations = Reservation.query.all()
        return [
            {
                "id": r.id,
                "user_id": r.user_id,
                "spot_id": r.spot_id,
                "lot_id": r.spot.lot_id if r.spot else None,
                "vehicle_number": r.vehicle_number,
                "start_time": dateFormat(r.start_time),
                "end_time": dateFormat(r.end_time),
                "cost": r.parking_fee,
            }
            for r in reservations
        ]


# -------- Summary & Reports --------
class SummaryResource(Resource):
    method_decorators = [admin_required]

    @cache.cached(timeout=180, key_prefix="summary_data")
    def get(self):
        total_users = User.query.count()
        active_reservations = Reservation.query.filter(
            Reservation.end_time == None
        ).count()
        lots = ParkingLot.query.count()

        revenue = db.session.query(
            func.strftime("%Y-%m", Reservation.start_time).label("month"),
            func.sum(Reservation.parking_fee).label("total")
        ).group_by("month").all()

        revenue_data = [{"month": r[0], "amount": float(r[1] or 0)} for r in revenue]

        return {
            "total_users": total_users,
            "active_reservations": active_reservations,
            "lots": lots,
            "revenue": revenue_data
        }


class OccupancyReportResource(Resource):
    method_decorators = [admin_required]

    @cache.cached(timeout=120, key_prefix="report_occupancy")
    def get(self):
        lots = ParkingLot.query.all()
        data = []
        for lot in lots:
            occupied = lot.occupied_spots
            available = lot.number_of_spots - occupied
            data.append({"lot": lot.name, "available": available, "occupied": occupied})
        return data

class RevenueReportResource(Resource):
    method_decorators = [admin_required]

    @cache.cached(timeout=120, key_prefix="report_revenue")
    def get(self):
        results = (
            db.session.query(
                ParkingLot.name,
                extract("month", Reservation.start_time).label("month"),
                func.sum(Reservation.parking_fee).label("revenue")
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
        if months_seen:
            min_month, max_month = min(months_seen), max(months_seen)
        else:
            return {"range": {"start": 1, "end": 0}, "data": {}}

        # Fill missing months with 0
        final_data = {}
        for lot, month_dict in data.items():
            final_data[lot] = {
                m: month_dict.get(m, 0.0) for m in range(min_month, max_month + 1)
            }

        return {
            "range": {"start": min_month, "end": max_month},
            "data": final_data
        }


class ReservationReportResource(Resource):
    method_decorators = [admin_required]
    
    @cache.cached(timeout=120, key_prefix="report_reservations")
    def get(self):
        results = (
            db.session.query(
                ParkingLot.name,
                func.count(Reservation.id).label("bookings")
            )
            .join(Reservation.spot)
            .join(ParkingLot)
            .group_by(ParkingLot.name)
            .all()
        )
        return [{"lot": lot, "bookings": bookings} for lot, bookings in results]


class PdfReportResource(Resource):
    method_decorators = [admin_required]

    def post(self):
        """Generate PDF with tables + charts"""
        data = request.get_json()
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
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        table.wrapOn(p, width, height)
        table.drawOn(p, 50, height - 200)

        # Revenue summary
        results = (
            db.session.query(
                ParkingLot.name,
                func.sum(Reservation.parking_fee).label("total_revenue")
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
        table2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        table2.wrapOn(p, width, height)
        table2.drawOn(p, 50, height - 400)

        # Charts
        p.showPage()
        y = height - 100
        for chart in charts:
            try:
                img_data = chart["data"].split(",")[1]
                img_bytes = base64.b64decode(img_data)
                img_buf = BytesIO(img_bytes)
                img_reader = ImageReader(img_buf)
                p.drawImage(img_reader, 50, y - 250, width=500, height=250,
                            preserveAspectRatio=True, mask="auto")
                y -= 300
                if y < 200:
                    p.showPage()
                    y = height - 100
            except Exception as e:
                print("Error embedding chart:", e)

        p.save()
        buffer.seek(0)
        return send_file(
            buffer, as_attachment=True,
            download_name="Parking_Report.pdf",
            mimetype="application/pdf"
        )

class SearchResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        search_type = request.args.get("type")
        search_by = request.args.get("search_by", "").strip()
        value = request.args.get("value", "").strip()

        if not search_type:
            return {"error": "Missing ?type= parameter"}, 400
        # if not value:
        #     return []

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
                query = query.join(Reservation).filter(Reservation.vehicle_number.ilike(f"%{value}%"))
            elif search_by == "driver":
                query = query.join(Reservation).filter(Reservation.driver_name.ilike(f"%{value}%"))
            elif search_by == "parking_lot":
                query = query.join(Reservation).join(ParkingSpot).join(ParkingLot).filter(ParkingLot.name.ilike(f"%{value}%"))
            return [u.to_dict() for u in query.all()]

        # -------- BOOKINGS --------
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
                query = query.join(ParkingSpot).join(ParkingLot).filter(ParkingLot.name.ilike(f"%{value}%"))

            return [r.get_details for r in query.all()]

        # -------- LOTS --------
        elif search_type == "lots":
            # Reuse existing service
            return get_all_lots(), 200

        # -------- BROAD QUERY (bquery) --------
        elif search_type == "bquery":
            results = search_all(value)
            return results, 200

        else:
            return {"error": f"Unsupported search type: {search_type}"}, 400

class ReminderLogsResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        """
        Admin:
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
            dt_from = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=utc)
            query = query.filter(ReminderJob.scheduled_at >= dt_from)

        if date_to:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(tzinfo=utc)
            query = query.filter(ReminderJob.scheduled_at <= dt_to)

        query = query.order_by(ReminderJob.scheduled_at.desc())

        page_obj = query.paginate(page=page, per_page=per_page, error_out=False)

        logs = []
        for job in page_obj.items:
            u = User.query.get(job.user_id)
            logs.append({
                "id": job.id,
                "user_id": job.user_id,
                "user_name": u.name if u else None,
                "scheduled_at": job.scheduled_at.isoformat(),
                "status": job.status,
                "sent_at": job.sent_at.isoformat() if job.sent_at else None,
                "error_message": getattr(job, "error_message", None),
                "created_at": job.created_at.isoformat(),
            })
        logs1 =[
            {
                "id": "12",
                "user_id": "34",
                "user_name":"test user",
                "scheduled_at": datetime.now().date().isoformat(),
                "status": "sent",
                "sent_at": datetime.now().isoformat(),
                "error_message": "None",
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "12",
                "user_id": "34",
                "user_name":"another user",
                "scheduled_at": datetime.now().date().isoformat(),
                "status": "sent",
                "sent_at": datetime.now().isoformat(),
                "error_message": "None",
                "created_at": datetime.now().isoformat(),
            }
            
        ]
        if len(logs)==0:
            return logs1
        return logs



api.add_resource(LotsResource, "/lots")
api.add_resource(LotResource, "/lots/<int:lot_id>")
api.add_resource(SlotResource, "/slots/<int:slot_id>")
api.add_resource(UsersResource, "/users")
api.add_resource(ReservationsResource, "/reservations")
api.add_resource(SummaryResource, "/summary")
api.add_resource(SearchResource, "/search")

api.add_resource(OccupancyReportResource, "/reports/occupancy")
api.add_resource(RevenueReportResource, "/reports/revenue")
api.add_resource(ReservationReportResource, "/reports/reservations")
api.add_resource(PdfReportResource, "/reports/pdf")
api.add_resource(ReminderLogsResource, "/reminders/logs")


 