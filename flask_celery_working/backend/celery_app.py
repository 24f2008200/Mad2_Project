
from backend.app import create_app
from backend.celery_instance import celery, init_celery_with_app

flask_app = create_app()
init_celery_with_app(flask_app)

__all__ = ("celery",)
