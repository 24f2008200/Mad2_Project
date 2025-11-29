# backend/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from redis import Redis

redis_conn = Redis(host='localhost', port=6379, db=1)
db = SQLAlchemy()
jwt = JWTManager()
cache = Cache()
