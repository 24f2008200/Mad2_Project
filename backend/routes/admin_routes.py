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

from backend.extensions import db, cache
from backend.models import ParkingLot, ParkingSpot, Reservation, User, dateFormat, search_all
from backend.routes.utils.auth import admin_required

from collections import defaultdict


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
api = Api(admin_bp)


# -------- Parking Lot Resources --------
class LotsResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        return  "To do", 200

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

    def get(self):
        
        return {
            "to do"
        }


class OccupancyReportResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        
        return "To do"

class RevenueReportResource(Resource):
    method_decorators = [admin_required]

    def get(self):
              
        return {
            "to do"
        }


class ReservationReportResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        
        return "to do"


class PdfReportResource(Resource):
    method_decorators = [admin_required]

    def post(self):
             
        return "to do"

class SearchResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        return "to do"


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

