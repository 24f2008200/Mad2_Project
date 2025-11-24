from flask import Blueprint, request
from flask_restful import Api, Resource
from backend.utils.auth import auth_required, current_user
from backend.services.reservation_service import reservation_service
from backend.utils.response import err

user_bp = Blueprint("user", __name__, url_prefix="/api/user")
api = Api(user_bp)

class SpotActivityResource(Resource):
    method_decorators = [auth_required]
    def post(self):
        data = request.get_json() or {}
        user = current_user()
        if data.get("action") == "book":
            return reservation_service.book_spot(
                user, data.get("lot_id"), data.get("vehicle_no"),
                data.get("driver_name"), data.get("driver_contact")
            )
        if data.get("action") == "release":
            return reservation_service.release_spot(user, data.get("reservation_id"))
        return err("Invalid action")

api.add_resource(SpotActivityResource, "/spots")
