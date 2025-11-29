# backend/tasks/export_tasks.py
import csv
import os
from datetime import datetime
from backend.extensions import  db,cache
from backend.celery_app import celery 
from backend.extensions import redis_conn
from backend.models import Reservation, ParkingSpot, ParkingLot

EXPORT_DIR = "exports"

@celery.task(bind=True)
def export_user_history_csv(self, user_id):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"user_{user_id}_history_{timestamp}.csv"
    filepath = os.path.join(EXPORT_DIR, filename)

    os.makedirs(EXPORT_DIR, exist_ok=True)

    # Fetch data
    records = (
        db.session.query(Reservation)
        .filter(Reservation.user_id == user_id)
        .all()
    )

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow([
            "reservation_id", "user_id", "lot", "spot_id",
            "vehicle_number", "driver_name",
            "start_time", "end_time", "duration_minutes",
            "cost", "remarks"
        ])

        for r in records:
            duration = None
            if r.end_time:
                duration = (r.end_time - r.start_time).total_seconds() // 60

            writer.writerow([
                r.id,
                r.user_id,
                r.spot.lot.name if r.spot else None,
                r.spot_id,
                r.vehicle_number,
                r.driver_name,
                r.start_time,
                r.end_time,
                duration,
                r.parking_fee,
                r.remarks,
            ])

    # Store result in redis
    redis_conn.set(f"task:{self.request.id}:result", filepath)

    return filepath
