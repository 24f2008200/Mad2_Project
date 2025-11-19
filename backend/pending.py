


# Add route in Flask:

# views/reports.py
from flask import Blueprint, jsonify, request
from backend.tasks_pending import generate_export_csv

bp = Blueprint("reports", __name__, url_prefix="/api/reports")

@bp.route("/export_csv", methods=["POST"])
def export_csv():
    # assume current_user is set via your auth mechanism
    user = current_user  # flask-login or token-based
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # enqueue task
    job = generate_export_csv.delay(user.id)
    return jsonify({"task_id": job.id, "status": "enqueued"}), 202


#===============================================================


# Optionally: return polling endpoint to check Celery task status:

@bp.route("/task_status/<task_id>")
def task_status(task_id):
    res = celery.AsyncResult(task_id)
    return jsonify({"id": task_id, "state": res.state, "result": res.result})



#=====================================================================

# Google Chat webhook example (payload)
def send_google_chat(webhook_url, text):
    payload = {"text": text}
    requests.post(webhook_url, json=payload, timeout=5)


# You can make the message richer by using cards or markdown supported by Chat.
#========================================================================================

# Security & privacy considerations

# Only send reports to user’s verified email / webhook associated to that user.

# Files should be private with presigned time-limited URLs.

# Do not place personal data in public buckets without auth.

# Rate-limit the export endpoint to avoid abuse (e.g. 1 export per minute per user).

# Sanitize/escape HTML in reports to prevent injection.

# 8) Edge cases & failure handling

# Tasks should catch exceptions and retry with exponential backoff (Celery supports autoretry_for decorator or retry()).

# If email fails, log and optionally resend later.

# For very large CSVs, use streaming generation to reduce memory.

# Example retry in Celery:

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_export_csv(self, user_id):
    try:
        ...
    except Exception as exc:
        raise self.retry(exc=exc)
#==================================================================================


# Tests & local workflow

# Start Redis: redis-server

# Start Celery worker: celery -A celery_app.celery worker --loglevel=info

# Start celery beat in a separate process: celery -A celery_app.celery beat --loglevel=info

# Use POST /api/reports/export_csv to enqueue an export.

# Manually test monthly runner by invoking tasks.monthly_report_runner.apply() or celery -A celery_app.celery call --task tasks.monthly_report_runner in dev.

# 10) Helpful DB migrations / model additions

# Add fields to User:

class User(db.Model):
    id = ...
    name = ...
    email = ...
    receive_reminders = db.Column(db.Boolean, default=True)
    reminder_time = db.Column(db.String(5), default="18:00")  # "HH:MM" in IST
    google_chat_webhook = db.Column(db.String(300), nullable=True)


# Add created_at to ParkingLot and Reservation (timestamps) if not present.



# Example: quick checklist to implement now

# Add fields receive_reminders, reminder_time, google_chat_webhook to User. Add timestamps to models.

# Add celery_app.py and tasks.py (from above).

# Configure SMTP env vars and APP_BASE_URL/REPORT_STORAGE_DIR.

# Start Redis, Celery worker, and beat.

# Add /api/reports/export_csv route.

# For production: implement S3 uploads and presigned links.

# Add unit tests for task functions and email sending (mock SMTP, requests).