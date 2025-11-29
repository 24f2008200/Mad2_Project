from celery import shared_task
import time
import random

@shared_task(bind=True,name="tasks.demo_task")
def demo_task(self):
    """Simple test task that sleeps randomly."""
    delay = random.randint(1, 5)
    time.sleep(delay)
    return {"message": "done", "delay": delay}

@shared_task(name="backend.tasks.simple.multiply")
def multiply(x, y):
    return x * y

@shared_task(bind=True,name="tasks.demo_fail")
def demo_fail(self):
    time.sleep(2)
    if random.random() < 0.3:
        raise Exception("Random failure")
    return "ok"