import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # Config
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "devsecret")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vehicle_parking.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # replace with env variable later

    # Init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    Migrate(app, db)

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.parking_routes import parking_bp
    from routes.reservation_routes import reservation_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(parking_bp, url_prefix="/parking")
    app.register_blueprint(reservation_bp, url_prefix="/reservation")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
