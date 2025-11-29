# backend/celery_app.py
# This file is the entrypoint for running the worker/beat process.
# Start worker with: celery -A backend.celery_app.celery worker -l info
# Start beat with:   celery -A backend.celery_app.celery beat -l info

from backend.app import create_app
from backend.celery_instance import celery, init_celery_with_app

# create Flask app *first*
flask_app = create_app()

# then configure / bind celery with that flask app
init_celery_with_app(flask_app)

# expose celery for `-A backend.celery_app.celery`
__all__ = ("celery",)
