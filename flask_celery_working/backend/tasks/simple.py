
from backend.celery_instance import celery

@celery.task(name="backend.tasks.simple.add")
def add(x, y):
    return x + y

@celery.task(name="backend.tasks.simple.ping")
def ping(x):
    return f"pong {x}"
