# backend/tasks/misc.py
from backend.celery_instance import celery


@celery.task
def test_add(x, y):
    print("Task running...", x, y)
    return x + y
    