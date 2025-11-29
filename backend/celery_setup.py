# backend/celery_setup.py
from backend.celery_instance import init_celery_with_app

def init_celery(app):
    init_celery_with_app(app)
