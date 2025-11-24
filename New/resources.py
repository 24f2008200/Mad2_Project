from functools import wraps
from flask_restful import Resource
from backend.utils.auth import current_user

class BaseResource(Resource):
    pass

class AuthResource(BaseResource):
    method_decorators = []

class AdminResource(BaseResource):
    method_decorators = []
