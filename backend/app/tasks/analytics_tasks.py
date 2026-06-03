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
    async def _aggregate():
        from datetime import datetime, timedelta, timezone

        from sqlalchemy import func, select
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from app.core.config import get_settings
        from app.models import AnalyticsEvent, Purchase, PurchaseStatus, User

        settings = get_settings()
        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        since = datetime.now(timezone.utc) - timedelta(days=1)

        async with async_session() as session:
            new_users = (
                await session.execute(
                    select(func.count(User.id)).where(User.created_at >= since)
                )
            ).scalar_one()
            purchases = (
                await session.execute(
                    select(func.count(Purchase.id)).where(
                        Purchase.status == PurchaseStatus.COMPLETED,
                        Purchase.created_at >= since,
                    )
                )
            ).scalar_one()
            events = (
                await session.execute(
                    select(func.count(AnalyticsEvent.id)).where(AnalyticsEvent.created_at >= since)
                )
            ).scalar_one()
            event = AnalyticsEvent(
                event_type="daily_aggregation",
                event_data={
                    "new_users": int(new_users or 0),
                    "purchases": int(purchases or 0),
                    "events": int(events or 0),
                },
            )
            session.add(event)
            await session.commit()

    logger.info("Running daily analytics aggregation")
    run_async(_aggregate())
