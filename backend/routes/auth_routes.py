
from flask import Blueprint, request, jsonify, session
from backend.extensions import db, bcrypt  
from backend.models import User
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Register 
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password required"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "User already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    user = User(
        email=data["email"],
        name=data.get("name", ""),
        password=hashed_password,
        is_admin=False
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


# Login
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    print(data)
    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token  = create_access_token(
        identity=str(user.id),  
        additional_claims={
        "email": user.email,
        "role": user.role,
        "is_admin": user.is_admin
        }
    )
    print(user.id, user.email, user.role)
    return jsonify({
        "access_token": token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "mobile": user.mobile,
            "is_admin": user.is_admin
        }
    }), 200
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"message": "Logged out"})

@auth_bp.route("/api/ping", methods=["GET", "OPTIONS"])
def ping():
    return {"message": "pong"}

