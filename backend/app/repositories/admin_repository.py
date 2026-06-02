from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AdminLog,
    AnalyticsEvent,
    Generation,
    GenerationStatus,
    Message,
    Transaction,
    TransactionType,
    User,
)


class AdminRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def log_action(
        self,
        admin_id: UUID,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> AdminLog:
        entry = AdminLog(
            admin_id=admin_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_logs(self, page: int = 1, page_size: int = 20) -> tuple[list[AdminLog], int]:
        total = (await self._session.execute(select(func.count(AdminLog.id)))).scalar_one()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(AdminLog).order_by(AdminLog.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_stats(self) -> dict:
        now = datetime.now(timezone.utc)
        since_24h = now - timedelta(hours=24)

        total_users = (await self._session.execute(select(func.count(User.id)))).scalar_one()
        active_users_24h = (
            await self._session.execute(
                select(func.count(User.id)).where(User.last_seen_at >= since_24h)
            )
        ).scalar_one()
        total_messages = (await self._session.execute(select(func.count(Message.id)))).scalar_one()
        total_generations = (
            await self._session.execute(select(func.count(Generation.id)))
        ).scalar_one()
        pending_generations = (
            await self._session.execute(
                select(func.count(Generation.id)).where(
                    Generation.status.in_([GenerationStatus.PENDING, GenerationStatus.PROCESSING])
                )
            )
        ).scalar_one()
        completed_generations = (
            await self._session.execute(
                select(func.count(Generation.id)).where(Generation.status == GenerationStatus.COMPLETED)
            )
        ).scalar_one()
        revenue = (
            await self._session.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    Transaction.type.in_([TransactionType.PURCHASE, TransactionType.BONUS])
                )
            )
        ).scalar_one()

        return {
            "total_users": total_users,
            "active_users_24h": active_users_24h,
            "total_messages": total_messages,
            "total_generations": total_generations,
            "total_revenue_gems": int(revenue or 0),
            "pending_generations": pending_generations,
            "completed_generations": completed_generations,
        }

    async def list_transactions(self, page: int = 1, page_size: int = 20) -> tuple[list[Transaction], int]:
        total = (await self._session.execute(select(func.count(Transaction.id)))).scalar_one()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(Transaction).order_by(Transaction.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def analytics_summary(self, days: int = 7) -> list[tuple[str, int]]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self._session.execute(
            select(AnalyticsEvent.event_type, func.count(AnalyticsEvent.id))
            .where(AnalyticsEvent.created_at >= since)
            .group_by(AnalyticsEvent.event_type)
            .order_by(func.count(AnalyticsEvent.id).desc())
        )
        return [(row[0], row[1]) for row in result.all()]

    async def total_chat_tokens(self) -> int:
        result = await self._session.execute(select(func.coalesce(func.sum(Message.tokens_used), 0)))
        return int(result.scalar_one() or 0)

    async def generation_status_counts(self) -> dict[str, int]:
        result = await self._session.execute(
            select(Generation.status, func.count(Generation.id)).group_by(Generation.status)
        )
        return {row[0].value: row[1] for row in result.all()}
