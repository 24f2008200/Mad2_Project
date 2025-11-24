from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from backend.models import User

def current_user():
    try:
        verify_jwt_in_request(optional=True)
        claims = get_jwt()
        uid = claims.get("sub") or claims.get("identity")
        return User.query.get(int(uid)) if uid else None
    except Exception:
        return None

def require_auth(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        verify_jwt_in_request()
        return fn(*a, **k)
    return wrapper

def require_role(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*a, **k):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return {"error": "Forbidden"}, 403
            return fn(*a, **k)
        return wrapper
    return decorator

auth_required = require_auth
admin_required = require_role("admin")
