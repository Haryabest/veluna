import asyncio
from uuid import UUID

from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task
def track_event(user_id: str | None, event_type: str, event_data: dict | None = None):
    async def _track():
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from app.core.config import get_settings
        from app.models import AnalyticsEvent

        settings = get_settings()
        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            event = AnalyticsEvent(
                user_id=UUID(user_id) if user_id else None,
                event_type=event_type,
                event_data=event_data or {},
            )
            session.add(event)
            await session.commit()

    run_async(_track())


@celery_app.task
def aggregate_daily_analytics():
    logger.info("Running daily analytics aggregation")
    track_event.delay(None, "daily_aggregation", {"status": "completed"})
