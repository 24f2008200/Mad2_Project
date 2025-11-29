# backend/celery_signals.py
from datetime import datetime
from celery.signals import task_prerun, task_postrun, task_failure, task_revoked
from flask import current_app
from backend.models import db, TaskRecord


@task_prerun.connect
def on_task_prerun(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    # signals run in the Celery process; we enter the Flask context explicitly
    with current_app.app_context():
        now = datetime.utcnow()
        rec = TaskRecord.query.get(task_id)
        if not rec:
            rec = TaskRecord(
                id=task_id,
                name=getattr(sender, "name", str(sender)),
                status="RUNNING",
                start_time=now,
                worker=kw.get("hostname"),
                progress=0,
            )
            db.session.add(rec)
        else:
            rec.status = "RUNNING"
            rec.start_time = now
            rec.worker = kw.get("hostname") or rec.worker
        db.session.commit()
        print(f"Task {task_id} started at {now}.")


@task_postrun.connect
def on_task_postrun(sender=None, task_id=None, task=None, retval=None, state=None, **kw):
    with current_app.app_context():
        now = datetime.utcnow()
        rec = TaskRecord.query.get(task_id)
        if not rec:
            # create minimal record if missing
            rec = TaskRecord(id=task_id, name=getattr(sender, "name", str(sender)))
            db.session.add(rec)

        rec.status = "SUCCESS"
        rec.end_time = now
        if rec.start_time:
            rec.duration = (rec.end_time - rec.start_time).total_seconds()
        rec.progress = 100
        db.session.commit()
        print(f"Task {task_id} completed successfully at {now}.")


@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, traceback=None, **kw):
    with current_app.app_context():
        now = datetime.utcnow()
        rec = TaskRecord.query.get(task_id)
        if not rec:
            rec = TaskRecord(id=task_id, name=getattr(sender, "name", str(sender)))
            db.session.add(rec)
        rec.status = "FAILED"
        rec.end_time = now
        if rec.start_time:
            rec.duration = (rec.end_time - rec.start_time).total_seconds()
        db.session.commit()
        print(f"Task {task_id} failed at {now}.")

@task_revoked.connect
def on_task_revoked(request=None, terminated=None, signum=None, expired=None, **kw):
    with current_app.app_context():
        task_id = getattr(request, "id", None) or kw.get("task_id")
        if not task_id:
            return
        rec = TaskRecord.query.get(task_id)
        if not rec:
            rec = TaskRecord(id=task_id, name="(revoked)")
            db.session.add(rec)
        rec.status = "REVOKED"
        rec.end_time = datetime.utcnow()
        if rec.start_time:
            rec.duration = (rec.end_time - rec.start_time).total_seconds()
        db.session.commit()
        print(f"Task {task_id} was revoked.")