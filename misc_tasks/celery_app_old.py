# backend/tasks/celery_app.py

import os
from celery import Celery

# Broker & backend
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Create Celery app
celery_app = Celery(
    "backend",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Important: Tell Celery where tasks live 
celery_app.autodiscover_tasks(packages=[
    "backend.tasks"
])

# Celery timezone settings
celery_app.conf.update(
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Periodic tasks (beat schedule)
celery_app.conf.beat_schedule = {
    "poll-rules-every-minute": {
        "task": "backend.tasks.tasks.poll_rules",
        "schedule": 60.0,  # every 1 minute
    },
}
