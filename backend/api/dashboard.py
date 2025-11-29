# backend/api/dashboard.py
from flask import Blueprint, request, jsonify, current_app
from backend.models import db, TaskRecord
from math import ceil
import redis
from celery import Celery

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

def get_celery_app() -> Celery:
    """Import or construct your celery app. Adapt to however you expose it in your project."""
    # e.g. from yourproject.celery_app import celery_app
    # return celery_app
    return current_app.extensions.get("celery")  # example if you registered celery in app.extensions

@dashboard_bp.route("/tasks")
def list_tasks():
    """
    GET /api/tasks?status=SUCCESS&worker=celery@worker1&page=1&limit=50
    """
    status = request.args.get("status", type=str)
    worker = request.args.get("worker", type=str)
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=50, type=int)
    q = TaskRecord.query

    if status:
        q = q.filter(TaskRecord.status == status)
    if worker:
        q = q.filter(TaskRecord.worker == worker)

    total = q.count()
    q = q.order_by(TaskRecord.created_at.desc()).offset((page - 1) * limit).limit(limit)
    tasks = [t.to_dict() for t in q]
    return jsonify({"tasks": tasks, "total": total, "page": page, "pages": ceil(total / limit) if limit else 1})

@dashboard_bp.route("/metrics")
def metrics():
    """
    GET /api/metrics
    Returns:
    {
      "workers": {"celery@worker1": "online", ...},
      "queue_length": 12,
      "avg_task_duration": 2.3,
      "success_rate": 0.95
    }
    """
    # Default responses
    resp = {
        "workers": {},
        "queue_length": None,
        "avg_task_duration": None,
        "success_rate": None
    }

    # 1) Workers health via celery inspect
    celery = get_celery_app()
    if celery:
        try:
            i = celery.control.inspect(timeout=1.0)
            pings = i.ping() or {}
            # ping returns {hostname: {'ok': 'pong'}}
            # mark online if present
            for host in pings.keys():
                resp["workers"][host] = "online"
            # We can attempt to list known workers registered to TaskRecord table too:
            # mark any worker found in DB but not in ping as offline
            known = {r.worker for r in TaskRecord.query.with_entities(TaskRecord.worker).distinct() if r.worker}
            for k in known:
                if k and k not in resp["workers"]:
                    resp["workers"].setdefault(k, "offline")
        except Exception:
            # fail gracefully, leave workers empty
            pass

    # 2) Queue length (Redis example) — adapt if you use a different broker.
    try:
        broker_url = current_app.config.get("CELERY_BROKER_URL") or current_app.config.get("BROKER_URL")
        if broker_url and broker_url.startswith("redis://"):
            # A simple approach: if you use default queue name "celery", the list key is "celery"
            # For Redis broker/transport, Celery uses list key(s) often like 'celery' or kombu.* keys.
            # You may prefer to compute length per-queue via redis. We'll attempt a common key.
            r = redis.StrictRedis.from_url(broker_url)
            # typical kombu default: stored in list named 'celery'
            try_keys = ["celery"]  # you can expand this list with your queue names
            length = 0
            for k in try_keys:
                try:
                    length += r.llen(k)
                except Exception:
                    pass
            resp["queue_length"] = length
        else:
            # unknown broker, leave as None
            resp["queue_length"] = None
    except Exception:
        resp["queue_length"] = None

    # 3) Average duration (last N tasks) and success rate
    try:
        # avg for last 1000 completed tasks (success+failed)
        recent = TaskRecord.query.filter(TaskRecord.duration.isnot(None)).order_by(TaskRecord.end_time.desc()).limit(1000).all()
        if recent:
            durations = [r.duration for r in recent if r.duration is not None]
            if durations:
                resp["avg_task_duration"] = round(sum(durations) / len(durations), 3)
        # success rate over last 1000 finished tasks
        finished = TaskRecord.query.filter(TaskRecord.status.in_(["SUCCESS", "FAILED", "REVOKED"])).order_by(TaskRecord.end_time.desc()).limit(1000).all()
        if finished:
            succ = sum(1 for r in finished if r.status == "SUCCESS")
            resp["success_rate"] = round(succ / len(finished), 3)
    except Exception:
        pass

    return jsonify(resp)
