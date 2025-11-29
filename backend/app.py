# backend/app.py
import sys
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate


from backend.config import Config
from backend.extensions import db, jwt, cache


my_app = None


# ============================================================
# CREATE FLASK APPLICATION
# ============================================================
def create_app():
    

    app = Flask(__name__, instance_relative_config=True)


    # Load EVERYTHING from config.py
    app.config.from_object(Config)
    for key, value in app.config.items():
        print(key, "=", value)


    # ------------------------------
    # CORS
    # ------------------------------

    CORS(app,
         resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
          methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    # ------------------------------
    # Cache (Redis or SimpleCache)supports_credentials=True,
    # ------------------------------
    cache.init_app(app)

    # ------------------------------
    # Extensions
    # ------------------------------
    db.init_app(app)
    jwt.init_app(app)
    Migrate(app, db)

    # ------------------------------
    # Blueprints
    # ------------------------------
    from backend.routes.auth_routes import auth_bp
    from backend.routes.admin_routes import admin_bp
    from backend.routes.user_routes import user_bp
    from backend.diagnostics import diagnostics_bp
    from backend.api.tasks import api_bp as tasks_api
    from backend.api.task_actions import task_actions_bp as task_actions_bp
    from backend.api.dashboard import dashboard_bp as dashboard_bp

    app.register_blueprint(diagnostics_bp, url_prefix="/api/admin")
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(tasks_api)
    app.register_blueprint(task_actions_bp)
    app.register_blueprint(dashboard_bp)

    print("Blueprints registered.")

    # ------------------------------
    # Celery ← bind to Flask app
    # ------------------------------ 
    # from .celery_utils import init_celery 
    from backend.celery_setup import init_celery
    from backend.celery_instance import celery
    init_celery(app)
    print("Celery initialized.")

    return app


# ============================================================
# DIRECT RUN MODE
# ============================================================
if __name__ == "__main__":
    app = create_app()
    my_app = app

    port = int(Config.__dict__.get("FLASK_PORT", 5000))
    print (f"Starting Flask app on port {port}...")
    print("CORS_ORIGINS =", app.config["CORS_ORIGINS"])
    app.run(debug=False, port=port, use_reloader=True)