# backend/api/task_actions.py

from flask import Blueprint, request, jsonify
from backend.tasks.simple import add
from backend.tasks.reports import export_user_history_csv
from backend.tasks.reminders import send_user_reminder
from backend.tasks.rules import run_rule

task_actions_bp = Blueprint("task_actions", __name__ ,url_prefix="/api/task_actions")

# ------------------------------------------------
# Simple test task
# ------------------------------------------------
@task_actions_bp.route("/tasks/add", methods=["POST"])
def run_add():
    data = request.json or {}
    x = data.get("x", 0)
    y = data.get("y", 0)
    task = add.delay(x, y)
    return jsonify({"task_id": task.id})


# ------------------------------------------------
# Export history
# ------------------------------------------------
@task_actions_bp.route("/tasks/export-history/<int:user_id>", methods=["POST"])
def run_export(user_id):
    task = export_user_history_csv.delay(user_id)
    return jsonify({"task_id": task.id})


# ------------------------------------------------
# Send reminder manually
# ------------------------------------------------
@task_actions_bp.route("/tasks/remind/<int:user_id>", methods=["POST"])
def run_manual_reminder(user_id):
    task = send_user_reminder.delay(user_id, {"channels": ["email", "gchat"]})
    return jsonify({"task_id": task.id})


# ------------------------------------------------
# Trigger a rule manually
# ------------------------------------------------
@task_actions_bp.route("/tasks/rules/run/<int:rule_id>", methods=["POST"])
def run_rule_now(rule_id):
    task = run_rule.delay(rule_id, None)
    return jsonify({"task_id": task.id})
