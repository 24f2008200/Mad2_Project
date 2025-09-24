import os ,sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

from backend.extensions import db, jwt ,cache

basedir = os.path.abspath(os.path.dirname(__file__))

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(os.path.dirname(BASE_DIR), "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)





def create_app(use_redis = False, large_data = 0):

    app = Flask(__name__, instance_relative_config=True)

    CORS(app,
     resources={r"/*": {"origins": "http://localhost:5173"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])
    if large_data == 2:
        data_base ='vehicle_parking_large.db'
    elif large_data == 1:
        data_base ='vehicle_parking_medium.db'
    else:
        data_base = 'vehicle_parking.db'
    print("Starting with data base:  " +data_base)


    # Config
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "devsecret")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "super-secret-key")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(INSTANCE_DIR, data_base)}"
    app.config["CORS_AUTOMATIC_OPTIONS"] = True

   



    db.init_app(app)
    jwt.init_app(app)


    

    from backend.routes.auth_routes import auth_bp
    from backend.routes.admin_routes import admin_bp
    from backend.routes.user_routes import user_bp
    from backend.diagnostics import diagnostics_bp

    app.register_blueprint(diagnostics_bp, url_prefix="/api/admin") 
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    print("Registered blueprints")
    return app

if __name__ == "__main__":
    use_redis = False
    large_data = False

    app = create_app(use_redis,large_data)
    port = int(os.environ.get("FLASK_PORT", 5000))

    app.run(debug=True, port=port)
