
import time, random
from backend.celery_instance import celery

@celery.task(name="backend.tasks.demo.random_sleep")
def random_sleep():
    delay = random.randint(1, 5)
    time.sleep(delay)
    return {"delay": delay}
