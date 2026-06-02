from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "veluna",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.generation_tasks",
        "app.tasks.chat_tasks",
        "app.tasks.analytics_tasks",
        "app.tasks.maintenance_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=30,
    task_max_retries=3,
    task_routes={
        "app.tasks.generation_tasks.*": {"queue": "generation_queue"},
        "app.tasks.chat_tasks.*": {"queue": "chat_queue"},
        "app.tasks.analytics_tasks.*": {"queue": "analytics_queue"},
        "app.tasks.maintenance_tasks.*": {"queue": "analytics_queue"},
    },
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "app.tasks.maintenance_tasks.cleanup_expired_sessions",
            "schedule": crontab(minute="*/30"),
        },
        "aggregate-analytics": {
            "task": "app.tasks.analytics_tasks.aggregate_daily_analytics",
            "schedule": crontab(hour=2, minute=0),
        },
        "cleanup-inactive-chats": {
            "task": "app.tasks.maintenance_tasks.cleanup_inactive_chats",
            "schedule": crontab(hour=3, minute=0),
        },
        "cleanup-stale-cache": {
            "task": "app.tasks.maintenance_tasks.cleanup_stale_cache",
            "schedule": crontab(hour="*/6"),
        },
        "cleanup-failed-generations": {
            "task": "app.tasks.maintenance_tasks.cleanup_failed_generations",
            "schedule": crontab(hour=4, minute=0),
        },
    },
)
