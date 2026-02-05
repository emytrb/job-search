from celery import Celery
from celery.schedules import crontab
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "job_searcher",
    broker=redis_url,
    backend=redis_url,
    include=[
        "workers.tasks.digest",
        "workers.tasks.analyzer_queue",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    worker_prefetch_multiplier=1,  # One task at a time for LLM workers
    task_routes={
        "workers.tasks.digest.*": {"queue": "digest"},
        "workers.tasks.analyzer_queue.*": {"queue": "llm"},
    },
    task_default_queue="llm",
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Send daily digest at 8 AM UTC
    "send-daily-digest": {
        "task": "workers.tasks.digest.send_daily_digest",
        "schedule": crontab(minute=0, hour=8),
    },
}
