# backend/tasks/reports.py
import os
import csv
from datetime import datetime

from backend.celery_instance import celery


from backend.extensions import db, redis_conn
from backend.models import Reservation, ParkingSpot, ParkingLot
from backend.utils.storage import upload_file_to_s3, presigned_url_for_key, S3_PREFIX


EXPORT_DIR = "reports"


# -----------------------------------------------------
# Export reservation history to CSV (Redis-backed result)
# -----------------------------------------------------
@celery.task(name="backend.tasks.reports.export_user_history_csv", bind=True)
def export_user_history_csv(self, user_id):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"user_{user_id}_history_{timestamp}.csv"
    filepath = os.path.join(EXPORT_DIR, filename)

    os.makedirs(EXPORT_DIR, exist_ok=True)

    records = db.session.query(Reservation).filter(
        Reservation.user_id == user_id
    ).all()

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
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

    redis_conn.set(f"task:{self.request.id}:result", filepath)
    return filepath


# -----------------------------------------------------
# Export user CSV (S3-backed)
# -----------------------------------------------------
@celery.task(name="backend.tasks.reports.export_user_csv")
def export_user_csv(export_job_id):
    from backend.models import ExportJob
    job = db.session.query(ExportJob).get(export_job_id)
    if not job:
        return

    job.status = "running"
    db.session.commit()

    user_id = job.user_id
    params = job.params or {}

    from_dt = params.get("from")
    to_dt = params.get("to")
    if from_dt:
        from_dt = datetime.fromisoformat(from_dt)
    if to_dt:
        to_dt = datetime.fromisoformat(to_dt)
    else:
        to_dt = datetime.utcnow()

    q = db.session.query(Reservation).filter(
        Reservation.user_id == user_id
    )
    if from_dt:
        q = q.filter(Reservation.start_time >= from_dt)
    if to_dt:
        q = q.filter(Reservation.start_time <= to_dt)

    rows = q.all()

    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmpname = tmp.name
    tmp.close()

    with open(tmpname, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "reservation_id", "spot_id",
            "start_time", "end_time",
            "parking_fee", "vehicle_number"
        ])
        for r in rows:
            writer.writerow([
                r.id, r.spot_id,
                r.start_time, r.end_time,
                r.parking_fee, r.vehicle_number
            ])

    # upload to S3
    import uuid
    file_key = f"{S3_PREFIX}/{user_id}/export_{job.id}_{uuid.uuid4().hex}.csv"
    upload_file_to_s3(tmpname, file_key)
    url = presigned_url_for_key(file_key)

    job.result_url = url
    job.status = "done"
    db.session.commit()

    return url
