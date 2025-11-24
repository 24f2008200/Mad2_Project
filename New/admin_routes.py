from flask import Blueprint, request
from flask_restful import Api, Resource
from backend.utils.auth import admin_required
from backend.services.parking_service import parking_service
from backend.utils.response import ok, err

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
api = Api(admin_bp)

class LotsResource(Resource):
    method_decorators = [admin_required]
    def get(self):
        return ok(parking_service.list_all_lots())
    def post(self):
        return ok(parking_service.create_lot(request.get_json() or {}), 201)

class LotResource(Resource):
    method_decorators = [admin_required]
    def put(self, lot_id):
        data = request.get_json() or {}
        lot = parking_service.get_lot(lot_id)
        if not lot:
            return err("Lot not found", 404)
        lot.name = data.get("name", lot.name)
        lot.price = data.get("price", lot.price)
        from backend.extensions import db
        db.session.commit()
        return ok({"message": "Parking lot updated"})
    def delete(self, lot_id):
        lot = parking_service.get_lot(lot_id)
        if not lot:
            return err("Lot not found", 404)
        return ok(parking_service.delete_lot(lot))

api.add_resource(LotsResource, "/lots")
api.add_resource(LotResource, "/lots/<int:lot_id>")
