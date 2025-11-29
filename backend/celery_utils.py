# backend/celery_utils.py
#not used anymore - moved to celery_setup.py
def init_celery(celery, app):
    """
    Bind Celery instance to Flask application.
    Called ONLY from celery_app.py.
    """

    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone=app.config.get("CELERY_TIMEZONE", "Asia/Kolkata"),
        enable_utc=True,
    )

    # Make Celery tasks run inside Flask context
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # Autodiscover tasks inside backend/
    celery.autodiscover_tasks(["tasks"])
