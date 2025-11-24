from datetime import datetime, timezone

from flask import Blueprint, request, session
from flask_restful import Api, Resource
from flask_jwt_extended import create_access_token

from backend.extensions import db
from backend.models import User
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
api = Api(auth_bp)


class RegisterResource(Resource):
    """User registration."""

    def post(self):
        data = request.get_json() or {}

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return {"error": "Email and password required"}, 400

        if User.query.filter_by(email=email).first():
            return {"error": "User already exists"}, 400

        user = User(
            email=email,
            name=data.get("name") or "",
            password=generate_password_hash(password),
            mobile=data.get("mobile") or "",
            address=data.get("address") or "",
            receive_reminders=(data.get("receive_reminders", "No") == "Yes"),
            reminder_time=data.get("reminder_time", "18:00"),
            google_chat_webhook=data.get("google_chat_hook"),
            role="user",
            is_admin=False,
            last_login=datetime.now(timezone.utc),
        )

        db.session.add(user)
        db.session.commit()

        return {"message": "User registered successfully"}, 201


class LoginResource(Resource):
    """Login and JWT issuance."""

    def post(self):
        data = request.get_json() or {}
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return {"error": "Email and password required"}, 400

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return {"error": "Invalid credentials"}, 401

        token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "email": user.email,
                "role": user.role,
                "is_admin": bool(user.is_admin),
            },
        )

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        return {
            "access_token": token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "mobile": user.mobile,
                "is_admin": bool(user.is_admin),
            },
        }, 200


class LogoutResource(Resource):
    """Stateless JWT doesn't need a backend logout, but we can drop session data."""

    def post(self):
        session.pop("user", None)
        return {"message": "Logged out"}, 200


class PingResource(Resource):
    """Health check endpoint."""

    def get(self):
        return {"message": "pong"}, 200

    def options(self):
        # For CORS pre-flight support
        return {}, 200


api.add_resource(RegisterResource, "/register")
api.add_resource(LoginResource, "/login")
api.add_resource(LogoutResource, "/logout")
api.add_resource(PingResource, "/ping")
