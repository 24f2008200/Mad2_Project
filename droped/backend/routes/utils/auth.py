import os
from functools import wraps
from flask import jsonify
from flask_jwt_extended import (
    verify_jwt_in_request,
    get_jwt_identity,
    jwt_required,
    get_jwt
)
from backend.app import db
from backend.models import User


def auth_required(fn):
    """
    Wrapper for jwt_required that can be toggled via ENFORCE_AUTH in .env
    """
    if os.getenv("ENFORCE_AUTH", "false").lower() == "true":
        return jwt_required()(fn)
    return fn


def current_user():
    """Return the logged-in User object based on JWT token, or None if auth is disabled."""
    # print(os.getenv("ENFORCE_AUTH"))

    if os.getenv("ENFORCE_AUTH", "false").lower() != "true":
        print("Auth disabled, returning dummy user")
        # Dummy user for testing
        return User(
            id=1,
            email="dummy_admin@example.com",
            name="Dummy Admin",
            is_admin=True
        )
    # print("Fetching current user from JWT")

    user_id = int(get_jwt_identity())   # "sub" → user id (as int after conversion)
    claims = get_jwt()
    email = claims["email"]
    is_admin = claims["is_admin"]
    # print(f"Current user ID from JWT: {user_id}")
    return db.session.get(User, user_id)


def admin_required(fn):
    """
    Require that the logged-in user is the superuser.
    When ENFORCE_AUTH is off, this always allows.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if os.getenv("ENFORCE_AUTH", "false").lower() != "true":
            return fn(*args, **kwargs)

        verify_jwt_in_request()
        user = current_user()
        if not user or not user.is_admin:
            return jsonify({"error": "Admin privileges required"}), 403
        return fn(*args, **kwargs)
    return wrapper