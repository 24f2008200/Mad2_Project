
from datetime import datetime
from celery.signals import task_prerun, task_postrun, task_failure
from flask import current_app
from backend.models import TaskRecord, db

@task_prerun.connect
def on_task_prerun(sender=None, task_id=None, **kw):
    with current_app.app_context():
        now = datetime.utcnow()
        rec = TaskRecord(id=task_id, name=sender.name, status="RUNNING", start_time=now,
                         worker=kw.get("hostname"), progress=0)
        db.session.merge(rec)
        db.session.commit()

@task_postrun.connect
def on_task_postrun(sender=None, task_id=None, **kw):
    with current_app.app_context():
        now = datetime.utcnow()
        rec = TaskRecord.query.get(task_id)
        rec.status = "SUCCESS"
        rec.end_time = now
        rec.duration = (now - rec.start_time).total_seconds()
        rec.progress = 100
        db.session.commit()

@task_failure.connect
def on_task_failure(sender=None, task_id=None, **kw):
    with current_app.app_context():
        rec = TaskRecord.query.get(task_id)
        rec.status = "FAILED"
        db.session.commit()
