from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import ParkingLot, db

bp = Blueprint("lots", __name__)

@bp.route("/", methods=["GET"])
def get_lots():
    lots = ParkingLot.query.all()
    return jsonify([{
        "id": l.id,
        "name": l.prime_location_name,
        "price": l.price_per_hour,
        "spots": l.number_of_spots,
        "address": l.address,
        "pincode": l.pin_code
    } for l in lots])

@bp.route("/", methods=["POST"])
@jwt_required()
def create_lot():
    identity = get_jwt_identity()
    if not identity.get("is_admin"):
        return jsonify({"msg": "Admins only"}), 403

    data = request.get_json()
    lot = ParkingLot(
        prime_location_name=data["name"],
        price_per_hour=data["price"],
        address=data.get("address"),
        pin_code=data.get("pincode"),
        number_of_spots=data.get("spots", 0),
    )
    db.session.add(lot)
    db.session.commit()
    return jsonify({"msg": "Lot created", "id": lot.id}), 201
