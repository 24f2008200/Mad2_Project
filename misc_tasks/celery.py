# backend/celery.py

from backend.celery_app import celery, init_celery
from backend.app import create_app

# Only load Flask app when Celery worker/beat imports this file
if __name__ != "__main__":
    from backend.app import create_app
    flask_app = create_app()
    init_celery(flask_app)
