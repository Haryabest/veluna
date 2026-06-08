from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task
def cleanup_expired_sessions():
    logger.info("Cleaning up expired sessions")


@celery_app.task
def cleanup_inactive_chats():
    logger.info("Cleaning up inactive chats older than 90 days")


@celery_app.task
def cleanup_stale_cache():
    from app.tasks.chat_tasks import run_async

    async def _cleanup():
        from app.services.chat_cache_service import chat_cache

        deleted = await chat_cache.invalidate_all()
        logger.info("Cleaned up %d stale chat cache keys", deleted)
        return deleted

    run_async(_cleanup())


@celery_app.task
def cleanup_failed_generations():
    logger.info("Cleaning up failed generations older than 7 days")
