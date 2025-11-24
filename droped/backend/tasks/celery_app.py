# celery_app.py
import os
from celery import Celery
from datetime import timedelta

# Flask app’s import path
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery = Celery(
    "backend.tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["backend.tasks.scheduled_tasks"],
)

# Optional configuration for retries, serialization, etc.
celery.conf.update(
    timezone="Asia/Kolkata",  # adjust for your primary user base
    enable_utc=True,
)

# -------------------------------
# Celery Beat Schedule Definition
# -------------------------------
celery.conf.beat_schedule = {
    "daily-reminder-planner": {
    "task": "tasks.daily_reminder_planner",
    "schedule": {
            "type": "crontab",
            "hour": 6,
            "minute": 0,
        },
    },
    "minute-executor": {
        "task": "tasks.minute_reminder_executor",
        "schedule": timedelta(minutes=1),
    },
    "monthly-report-runner": {
        "task": "tasks.monthly_report_runner",
        # Runs at 06:00 IST on the first day of each month
        "schedule": {
            "type": "crontab",
            "hour": 6,
            "minute": 0,
            "day_of_month": 1,
        },
    },
}
