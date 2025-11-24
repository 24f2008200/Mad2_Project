from flask import Blueprint, app, jsonify, request
from backend.app import db 
from backend.models import Reservation


diagnostics_bp = Blueprint("diagnostics", __name__)


@diagnostics_bp.before_request
def log_request():
    print(" Request:", request.method, request.path)
# Perform diagnostics logic here
@diagnostics_bp.route("/diagnostics", methods=["GET", "POST"])
def diagnostics():
    data = request.json
    rs = Reservation.query.filter(
    Reservation.end_time != None,
    Reservation.start_time != None,
    # ((Reservation.parking_fee == 0) | (Reservation.parking_fee == None))
        ).all()
    sum = 0
    for r in rs:
        delta = r.end_time - r.start_time
        hours = delta.total_seconds() / 3600
        fee = round(hours * 10, 2)  # Assuming a rate of 10 per hour
        r.parking_fee = fee
        db.session.add(r)
        sum += fee
    db.session.commit()
    return jsonify({"status": "success", "data": data, "total_fee": sum}), 200


    