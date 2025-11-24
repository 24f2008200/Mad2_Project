
from time import timezone
from datetime import timedelta, timezone, datetime
from flask import request, session, Blueprint
from flask_restful import Resource, Api
from backend.extensions import db
from backend.models import User
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
api = Api(auth_bp)

class RegisterResource(Resource):
    def post(self):
        data = request.get_json()
        if not data or "email" not in data or "password" not in data:
            return {"error": "Email and password required"}, 400

        if User.query.filter_by(email=data["email"]).first():
            return {"error": "User already exists"}, 400

        hashed_password = generate_password_hash(data["password"])
        user = User(
            email=data["email"],
            name=data.get("name", ""),
            password=hashed_password,
            mobile=data.get("mobile", ""),
            address=data.get("address", ""),
            receive_reminders=data.get("receive_reminders", "No") == "Yes",
            reminder_time=data.get("reminder_time", "18:00"),
            google_chat_webhook=data.get("google_chat_hook", None),
            role="user",
            is_admin=False,
            last_login=datetime.now(timezone.utc),
        )
        db.session.add(user)
        db.session.commit()

        return {"message": "User registered successfully"}, 201


class LoginResource(Resource):
    def post(self):
        data = request.get_json()
        if not data or "email" not in data or "password" not in data:
            return {"error": "Email and password required"}, 400

        user = User.query.filter_by(email=data["email"]).first()
        if not user or not check_password_hash(user.password, data["password"]):
            return {"error": "Invalid credentials"}, 401

        token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "email": user.email,
                "role": user.role,
                "is_admin": user.is_admin,
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
                "is_admin": user.is_admin,
            },
        }, 200


class LogoutResource(Resource):
    def post(self):
        session.pop("user", None)
        return {"message": "Logged out"}, 200


class PingResource(Resource):
    def get(self):
        return {"message": "pong"}, 200

    def options(self):
        return {}, 200


api.add_resource(RegisterResource, "/register")
api.add_resource(LoginResource, "/login")
api.add_resource(LogoutResource, "/logout")
api.add_resource(PingResource, "/ping")
