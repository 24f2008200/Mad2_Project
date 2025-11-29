
from backend.app import db
from datetime import datetime

class TaskRecord(db.Model):
    id = db.Column(db.String(128), primary_key=True)
    name = db.Column(db.String(256))
    status = db.Column(db.String(32))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Float)
    worker = db.Column(db.String(128))
    progress = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
