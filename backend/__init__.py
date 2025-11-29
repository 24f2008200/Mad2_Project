# backend/__init__.py
from flask import Flask
from .config import Config

# import celery_init AFTER config to avoid circular imports
# from .celery_utils import init_celery
from .celery_setup import init_celery


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Celery with Flask's config
    init_celery(app)

    # register blueprints later...
    # from .routes import api
    # app.register_blueprint(api)

    return app
