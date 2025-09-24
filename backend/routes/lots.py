from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.models import ParkingLot, db
from backend.utils.auth import auth_required, admin_required, current_user

bp = Blueprint("lots", __name__)

@bp.route("/", methods=["GET"])
def get_lots():
    lots = ParkingLot.query.all()
    return jsonify([{
        "id": l.id,
        "name": l.name,
        "price": l.price,
        "spots": l.number_of_spots,
        "address": l.address,
        "pincode": l.pin_code
    } for l in lots])

@bp.route("/", methods=["POST"])
@jwt_required()
@admin_required
def create_lot():
    # user = current_user()
    # if not user or not user.is_admin:
    #     return jsonify({"msg": "Admins only"}), 403

    data = request.get_json()
    lot = ParkingLot(
        name=data["name"],
        price=data["price"],
        address=data.get("address"),
        pin_code=data.get("pincode"),
        number_of_spots=data.get("spots", 0),
    )
    db.session.add(lot)
    db.session.commit()
    return jsonify({"msg": "Lot created", "id": lot.id}), 201
