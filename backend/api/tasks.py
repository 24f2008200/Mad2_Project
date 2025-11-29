from flask import Blueprint, jsonify, request
from celery.result import AsyncResult
from backend.celery_instance import celery
from backend.models import TaskRecord

api_bp = Blueprint("tasks_api", __name__, url_prefix="/api/tasks")


# -------------------------------------------------------
# LIST ALL TASKS (from Celery result backend)
# -------------------------------------------------------
@api_bp.get("")
def list_tasks():
    """
    Return all tasks stored in DB for your dashboard table.
    """
    rows = TaskRecord.query.order_by(TaskRecord.created_at.desc()).limit(200).all()

    data = []
    for r in rows:
        data.append({
            "id": r.id,
            "name": r.name,
            "status": r.status,
            "worker": r.worker,
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "end_time": r.end_time.isoformat() if r.end_time else None,
            "duration": r.duration,
            "progress": r.progress,
        })

    return jsonify({"tasks": data})


def list_tasks_backend():
    """
    Lists all Celery tasks currently stored in the result backend.
    Guaranteed safe because we use celery.backend.get_all().
    """

    backend = celery.backend
    print(f"Backend type: {type(backend)}")

    # Celery >=5 provides this API, if Redis/DB backend supports it.
    # For Redis it works well.
    try:
        stored = backend._get_all()   # private but stable for Celery 5.x
    except:
        stored = {}
    print(f"Stored tasks: {len(stored)}")

    tasks = []
    for task_id, meta in stored.items():
        res = AsyncResult(task_id, app=celery)
        tasks.append({
            "id": task_id,
            "status": res.status,
            "result": meta.get("result"),
            "date_done": str(meta.get("date_done")),
        })

    return jsonify(tasks)


# -------------------------------------------------------
# GET SINGLE TASK
# -------------------------------------------------------
@api_bp.get("/<task_id>")
def get_task(task_id):
    res = AsyncResult(task_id, app=celery)

    return jsonify({
        "id": task_id,
        "status": res.status,
        "result": res.result if res.successful() else None,
        "traceback": res.traceback,
        "date_done": str(res.date_done) if res.date_done else None
    })


# -------------------------------------------------------
# CANCEL A TASK (revoke)
# -------------------------------------------------------
@api_bp.post("/<task_id>/cancel")
def cancel_task(task_id):

    celery.control.revoke(task_id, terminate=True)

    return jsonify({"canceled": True, "task_id": task_id})


# -------------------------------------------------------
# RUN ANY TASK MANUALLY
# -------------------------------------------------------
@api_bp.post("/run")
def run_task():
    data = request.json or {}
    task_name = data.get("task")
    args = data.get("args", [])
    kwargs = data.get("kwargs", {})

    if not task_name:
        return jsonify({"error": "Missing task name"}), 400

    try:
        # dynamically run any Celery task
        result = celery.send_task(task_name, args=args, kwargs=kwargs)
        return jsonify({"task_id": result.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
