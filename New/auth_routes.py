from flask import Blueprint, request
from flask_restful import Api, Resource
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from backend.extensions import db
from backend.models import User
from backend.utils.response import ok, err
import datetime

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
api = Api(auth_bp)

class RegisterResource(Resource):
    def post(self):
        data = request.get_json() or {}
        if not data.get("email") or not data.get("password"):
            return err("Email and password required", 400)
        if User.query.filter_by(email=data["email"]).first():
            return err("User already exists", 400)
        user = User(
            email=data["email"],
            name=data.get("name",""),
            password=generate_password_hash(data["password"]),
            role="user",
            is_admin=False,
        )
        db.session.add(user)
        db.session.commit()
        return ok({"message": "User registered successfully"}, 201)

class LoginResource(Resource):
    def post(self):
        data = request.get_json() or {}
        user = User.query.filter_by(email=data.get("email")).first()
        if not user or not check_password_hash(user.password, data.get("password","")):
            return err("Invalid credentials", 401)
        token = create_access_token(identity=str(user.id),
                                    additional_claims={"role": user.role, "is_admin": user.is_admin})
        user.last_login = datetime.datetime.now(datetime.timezone.utc)
        db.session.commit()
        return ok({"access_token": token,
                   "user": {"id": user.id, "email": user.email, "role": user.role}})

api.add_resource(RegisterResource, "/register")
api.add_resource(LoginResource, "/login")
