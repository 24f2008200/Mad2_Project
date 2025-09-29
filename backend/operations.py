from flask import Blueprint, request, jsonify, send_file
from sqlalchemy import func ,extract
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
from io import BytesIO
import base64

from backend.extensions import db,cache
from backend.models import ParkingLot, ParkingSpot, Reservation, User
from backend.routes.utils.auth import auth_required , admin_required
from backend.services.parking_service import get_all_lots


# Create parking lot
def create_lot():
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

    # Create spots 
    for i in range(lot.number_of_spots):
        spot = ParkingSpot(lot_id=lot.id, label=f"{lot.prefix}pot-{i+1}")
        db.session.add(spot)
    db.session.commit()
    cache.delete("all_lots")

    return jsonify({"message": "Parking lot created", "id": lot.id}), 201

# Get all parking lots with their spots

def list_lots():
    return get_all_lots(), 200

# View all users

def list_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "email": u.email,
                     "name": u.name, "mobile": u.mobile,
                     "address": u.address, "is_blocked": u.is_admin < 0  } for u in users])


def search_bookings():
    res = Reservation


def search_users():
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify([])

    results = User.query.filter(
        (User.email.ilike(f"%{query}%")) |
        (User.mobile.ilike(f"%{query}%")) |
        (User.name.ilike(f"%{query}%"))
    ).all()

    return jsonify([
        {"id": u.id, "email": u.email, "mobile": u.mobile, "name": u.name}
        for u in results
    ])

# Delete parking slot

def delete_parking_slot(slot_id):
    slot = ParkingSpot.query.get_or_404(int(slot_id))
    if slot.status == "O":
        return jsonify({"error": "Cannot delete occupied slot"}), 400
    lot = slot.lot
    lot.delete_spot(slot.id)  
    db.session.commit()
    cache.delete("all_lots")

    return jsonify({"message": "Parking slot deleted"}), 200

# Update parking lot

def update_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    data = request.get_json()
    try :
        lot.resize_spots(data.get("number_of_spots", lot.number_of_spots))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    lot.name = data.get("name", lot.name)
    lot.price = data.get("price", lot.price)
    lot.address = data.get("address", lot.address)
    lot.pin_code = data.get("pin_code", lot.pin_code)
    db.session.commit()
    cache.delete("all_lots")

    return jsonify({"message": "Parking lot updated"}), 200

# Delete parking lot

def delete_parking_lot(lot_id):
    lot = db.session.get(ParkingLot, lot_id)
    if not lot:
        return jsonify({"error": "Lot not found"}), 404

    if ParkingSpot.query.filter_by(lot_id=lot.id, status="O").count() > 0:
        return jsonify({"error": "Cannot delete lot with active spots"}), 400

    db.session.delete(lot)
    db.session.commit()
    cache.delete("all_lots")
    return jsonify({"message": "Lot deleted"}), 200


def summary():
    total_users = User.query.count()
    # blocked_users = User.query.filter_by(is_blocked=True).count()

    # Example: total active reservations
    from backend.models import Reservation, ParkingLot

    active_reservations = Reservation.query.filter(
        Reservation.end_time == None
    ).count()

    lots = ParkingLot.query.count()

    # Revenue by month
    revenue = db.session.query(
        func.strftime("%Y-%m", Reservation.start_time).label("month"),
        func.sum(Reservation.parking_fee).label("total")
    ).group_by("month").all()

    revenue_data = [{"month": r[0], "amount": float(r[1] or 0)} for r in revenue]

    return jsonify({
        "total_users": total_users,
        # "blocked_users": blocked_users,
        "active_reservations": active_reservations,
        "lots": lots,
        "revenue": revenue_data
    })


def list_reservations():
    reservations = Reservation.query.all()
    return jsonify([
        {
            "id": r.id,
            "user_id": r.user_id,
            "spot_id": r.spot_id,
            "lot_id": r.lot_id,
            "vehicle_number": r.vehicle_number,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "cost": r.cost,
        }
        for r in reservations
    ])

def search_users_admin():
    search_by = request.args.get("search_by")
    value = request.args.get("value")

    query = User.query
    if search_by == "name":
        query = query.filter(User.name.ilike(f"%{value}%"))
    elif search_by == "telephone":
        query = query.filter(User.mobile.ilike(f"%{value}%"))
    elif search_by == "address":
        query = query.filter(User.address.ilike(f"%{value}%"))
    elif search_by == "vehicle":
        query = query.join(Reservation).filter(Reservation.vehicle_number.ilike(f"%{value}%"))
    elif search_by == "parking_lot":
        query = query.join(Reservation).join(ParkingSpot).join(ParkingLot).filter(ParkingLot.name.ilike(f"%{value}%"))
    elif search_by == "mobile":
        query = query.filter(User.mobile.ilike(f"%{value}%"))
    elif search_by == "email":
        query = query.filter(User.email.ilike(f"%{value}%"))
    elif search_by == "driver":
        query = query.join(Reservation).filter(Reservation.driver_name.ilike(f"%{value}%"))
    elif search_by == "parking_lot":
        query = query.join(Reservation).join(ParkingSpot).join(ParkingLot).filter(ParkingLot.name.ilike(f"%{value}%"))

    return jsonify([u.to_dict() for u in query.all()])


def search_bookings_admin():
    search_by = request.args.get("search_by")
    value = request.args.get("value")

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

    return jsonify([r.to_dict() for r in query.all()])


def occupancy_report():
    lots = ParkingLot.query.all()
    data = []
    for lot in lots:
        occupied = lot.occupied_spots
        available = lot.number_of_spots - occupied
        data.append({
            "lot": lot.name,
            "available": available,
            "occupied": occupied
        })
    return jsonify(data)



def revenue_report():
    # revenue trend: group by month + lot
    results = (
    db.session.query(
        ParkingLot.name,
        extract("month", Reservation.start_time).label("month"),
        func.sum(Reservation.parking_fee).label("revenue")
        )
        .join(Reservation.spot)          # join Spot from Reservation
        .join(ParkingLot)                # join ParkingLot from Spot
        .group_by(ParkingLot.name, "month")
        .all()
        )
    
    data = {}
    for lot, month, revenue in results:
        if lot not in data:
            data[lot] = {}
        data[lot][int(month)] = float(revenue or 0)
    return jsonify(data)


def reservation_report():
    results = (
        db.session.query(
            ParkingLot.name,
            func.count(Reservation.id).label("bookings")
        )
        .join(Reservation.spot)          # join Spot from Reservation
        .join(ParkingLot)                # join ParkingLot from Spot
        .group_by(ParkingLot.name)
        .all()
    )
    data = [{"lot": lot, "bookings": bookings} for lot, bookings in results]
    return jsonify(data)


def generate_pdf():
    data = request.get_json()
    charts = data.get("charts", [])

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # ----------------------------
    # Page 1: Title + Tables
    # ----------------------------
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Parking Lot Monthly Report")

    # Occupancy summary table
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

    # Revenue summary table
    results = (
        db.session.query(
            ParkingLot.name,
            func.sum(Reservation.parking_fee).label("total_revenue")
        )
        .join(Reservation.spot)          # join Spot from Reservation
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

    # Finish Page 1
    p.showPage()

    # ----------------------------
    # Page 2+: Charts
    # ----------------------------
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

    # Save PDF
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name="Parking_Report.pdf",
                     mimetype="application/pdf")
