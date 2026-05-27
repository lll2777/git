from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ai_data_analysis",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.datasets"],
)

celery_app.conf.update(
    task_acks_late=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.datasets.analyze_dataset": {"queue": "analysis"},
    },
)
