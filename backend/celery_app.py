# celery_app.py
from celery import Celery
from celery.schedules import crontab

def make_celery(app_name=__name__):
    broker = "redis://localhost:6379/0"
    backend = "redis://localhost:6379/1"
    celery = Celery(app_name, broker=broker, backend=backend)
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Kolkata',
        enable_utc=False,
    )
    return celery

celery = make_celery()




celery.conf.beat_schedule = {
    # daily reminders: run every day at 18:00 IST (example). We'll personalize times per user in the task.
    'daily_reminder_cron': {
        'task': 'tasks.daily_reminder_runner',
        'schedule': crontab(minute=0, hour=12),  # run every day at 12:00 UTC (18:30 IST approx) adjust as needed
    },
    # monthly reports: run on the 1st of every month at 02:00 IST (example)
    'monthly_report_cron': {
        'task': 'tasks.monthly_report_runner',
        'schedule': crontab(minute=0, hour=20, day_of_month='1'),  # adjust for UTC->IST etc.
    },
}


# Integrate Celery with Flask when needed, but tasks can import the DB session via your app factory pattern.

#NOTE: We schedule a runner which then checks users' preferred reminder times. This avoids scheduling one task per user in beat.