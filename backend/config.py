# backend/config.py
import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

class Config:
    """
    Master configuration for the Parking Backend.
    All environment overrides happen here.
    """
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    # -------------------------------
    # Secret Keys
    # -------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "devsecret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretjwtkey")

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # -------------------------------
    # Database (SQLite dynamic) 
    # -------------------------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(os.path.dirname(BASE_DIR), "instance")
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    DATA_SIZE = int(os.getenv("DATA_SIZE", 0))  # 0=small,1=medium,2=large
    if DATA_SIZE == 2:
        DB_NAME = "vehicle_parking_large.db"
    elif DATA_SIZE == 1:
        DB_NAME = "vehicle_parking_medium.db"
    else:
        DB_NAME = "vehicle_parking.db"

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(INSTANCE_DIR, DB_NAME)}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------------------
    # Redis / Cache
    # USE_REDIS=true to enable
    # -------------------------------
    USE_REDIS = os.getenv("USE_REDIS", "false").lower() in ("1", "true", "yes", "on")

    # Default: SimpleCache
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 60

    # Redis override if enabled
    if USE_REDIS:
        CACHE_TYPE = "RedisCache"
        CACHE_REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        CACHE_REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        CACHE_REDIS_DB = int(os.getenv("REDIS_DB", 1))
        CACHE_DEFAULT_TIMEOUT = 300

    # -------------------------------
    # CORS Origins
    # -------------------------------
    CORS_ORIGINS = [
        os.getenv("CORS_ORIGIN_1"),
        os.getenv("CORS_ORIGIN_2"),
        os.getenv("CORS_ORIGIN_3"),
        os.getenv("CORS_ORIGIN_4"),
    ]

    CORS_AUTOMATIC_OPTIONS = True

    # -------------------------------
    # Celery
    # -------------------------------
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

    CELERY_TASK_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_TIMEZONE = "Asia/Kolkata"
    CELERY_ENABLE_UTC = True

    # -------------------------------
    # Storage / S3 (used in exports)
    # -------------------------------
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    S3_BUCKET = os.getenv("S3_BUCKET", "my-bucket")
    S3_REGION = os.getenv("S3_REGION", "ap-south-1")
    S3_PREFIX = os.getenv("S3_PREFIX", "exports")

    # -------------------------------
    # Email
    # -------------------------------
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
