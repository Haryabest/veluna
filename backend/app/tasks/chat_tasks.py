from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task
def process_chat_analytics(user_id: str, chat_id: str, tokens_used: int):
    logger.info("Chat analytics: user=%s chat=%s tokens=%d", user_id, chat_id, tokens_used)


@celery_app.task(bind=True, max_retries=3)
def process_ai_response(self, chat_id: str, message_id: str):
    """Background AI response processing for WebSocket chat."""
    logger.info("Processing AI response for chat %s message %s", chat_id, message_id)
