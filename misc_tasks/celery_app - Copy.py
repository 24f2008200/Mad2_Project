# backend/celery.py

import os
from celery import Celery

# Redis config
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Create Celery app
celery = Celery(
    "backend",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Autodiscover tasks inside backend/tasks/
celery.autodiscover_tasks([
    "backend.tasks"
])

# Global configuration
celery.conf.update(
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Beat schedule (run poller every minute)
celery.conf.beat_schedule = {
    "poll-rules-every-minute": {
        "task": "backend.tasks.tasks.poll_rules",
        "schedule": 60.0,
    },
}

# Force import modules so tasks actually register
import backend.tasks.tasks
import backend.tasks.scheduled_tasks
import backend.tasks.export_tasks

print("Celery app loaded — task modules imported.")
