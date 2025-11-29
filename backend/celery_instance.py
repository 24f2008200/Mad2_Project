# backend/celery_instance.py
from celery import Celery

# Create the Celery instance *without* binding Flask app yet.
# Tasks can safely `from backend.celery_instance import celery`

celery = Celery("parking_app")

def init_celery_with_app(app):
    celery.conf.update(
        broker_url = app.config["CELERY_BROKER_URL"],
        result_backend = app.config["CELERY_RESULT_BACKEND"],
        task_serializer = "json",
        result_serializer = "json",
        accept_content = ["json"],
        timezone = app.config["CELERY_TIMEZONE"],
        enable_utc = True,
        #  Add Beat Schedule here
        beat_schedule={
            "run-demo-task-every-10-seconds": {
                "task": "tasks.demo_task",
                "schedule": 10.0,
            },
            "run-failing-task-every-20-seconds": {
                "task": "tasks.demo_fail",
                "schedule": 20.0,
            },
            # add more repeating tasks here…
        },
    )
    celery.conf.flask_app = app
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            from flask import current_app
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    celery.autodiscover_tasks(["backend.tasks"])


    # Import signals AFTER celery is configured and app exists so signals
    # attach to the correct app and can use current_app
    import backend.services.celery_signals  # noqa: F401
