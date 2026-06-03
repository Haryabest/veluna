from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AdminLog,
    AnalyticsEvent,
    Chat,
    Generation,
    GenerationStatus,
    Message,
    PromoCode,
    Purchase,
    PurchaseStatus,
    ShopProduct,
    Transaction,
    TransactionType,
    User,
    UserBalance,
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
        since_7d = now - timedelta(days=7)

        total_users = (await self._session.execute(select(func.count(User.id)))).scalar_one()
        banned_users = (
            await self._session.execute(
                select(func.count(User.id)).where(User.is_banned == True)  # noqa: E712
            )
        ).scalar_one()

        users_with_chats = select(Chat.user_id).where(Chat.message_count > 0)
        users_with_generations = select(Generation.user_id)
        users_with_purchases = select(Purchase.user_id).where(
            Purchase.status == PurchaseStatus.COMPLETED
        )
        unique_users_ever = (
            await self._session.execute(
                select(func.count(User.id)).where(
                    or_(
                        User.id.in_(users_with_chats),
                        User.id.in_(users_with_generations),
                        User.id.in_(users_with_purchases),
                    )
                )
            )
        ).scalar_one()

        active_chat_users_24h = select(Chat.user_id).where(Chat.last_message_at >= since_24h)
        active_chat_users_7d = select(Chat.user_id).where(Chat.last_message_at >= since_7d)
        active_users_24h = (
            await self._session.execute(
                select(func.count(User.id)).where(
                    User.is_banned == False,  # noqa: E712
                    or_(
                        User.last_seen_at >= since_24h,
                        User.id.in_(active_chat_users_24h),
                    ),
                )
            )
        ).scalar_one()
        active_users_7d = (
            await self._session.execute(
                select(func.count(User.id)).where(
                    User.is_banned == False,  # noqa: E712
                    or_(
                        User.last_seen_at >= since_7d,
                        User.id.in_(active_chat_users_7d),
                    ),
                )
            )
        ).scalar_one()

        payments_row = (
            await self._session.execute(
                select(
                    func.count(Purchase.id),
                    func.coalesce(func.sum(Purchase.gems_amount), 0),
                    func.coalesce(func.sum(Purchase.stars_amount), 0),
                ).where(Purchase.status == PurchaseStatus.COMPLETED)
            )
        ).one()
        payments_count, payments_gems_total, payments_stars_total = payments_row

        revenue_tx = (
            await self._session.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    Transaction.type.in_([TransactionType.PURCHASE, TransactionType.BONUS])
                )
            )
        ).scalar_one()
        revenue_gems_total = int(payments_gems_total or 0) + int(revenue_tx or 0)

        expenses_tx = (
            await self._session.execute(
                select(func.coalesce(func.sum(func.abs(Transaction.amount)), 0)).where(
                    Transaction.type == TransactionType.SPEND
                )
            )
        ).scalar_one()
        expenses_balance = (
            await self._session.execute(select(func.coalesce(func.sum(UserBalance.total_spent), 0)))
        ).scalar_one()
        expenses_gems_total = int(max(expenses_tx or 0, expenses_balance or 0))

        usage_seconds = (
            await self._session.execute(
                select(
                    func.coalesce(
                        func.sum(
                            func.extract("epoch", Chat.last_message_at)
                            - func.extract("epoch", Chat.created_at)
                        ),
                        0,
                    )
                ).where(
                    Chat.last_message_at.isnot(None),
                    Chat.last_message_at > Chat.created_at,
                )
            )
        ).scalar_one()
        usage_time_minutes = int(float(usage_seconds or 0) // 60)
        avg_usage_minutes_per_user = (
            round(usage_time_minutes / unique_users_ever, 1) if unique_users_ever else 0.0
        )

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

        active_promos = (
            await self._session.execute(
                select(func.count(PromoCode.id)).where(PromoCode.is_active == True)  # noqa: E712
            )
        ).scalar_one()
        total_promos = (await self._session.execute(select(func.count(PromoCode.id)))).scalar_one()
        active_products = (
            await self._session.execute(
                select(func.count(ShopProduct.id)).where(ShopProduct.is_active == True)  # noqa: E712
            )
        ).scalar_one()
        total_products = (await self._session.execute(select(func.count(ShopProduct.id)))).scalar_one()

        return {
            "total_users": total_users,
            "unique_users_ever": unique_users_ever,
            "active_users_24h": active_users_24h,
            "active_users_7d": active_users_7d,
            "banned_users": banned_users,
            "payments_count": payments_count,
            "payments_gems_total": int(payments_gems_total or 0),
            "payments_stars_total": int(payments_stars_total or 0),
            "revenue_gems_total": revenue_gems_total,
            "expenses_gems_total": expenses_gems_total,
            "usage_time_minutes": usage_time_minutes,
            "avg_usage_minutes_per_user": avg_usage_minutes_per_user,
            "total_messages": total_messages,
            "total_generations": total_generations,
            "total_revenue_gems": revenue_gems_total,
            "pending_generations": pending_generations,
            "completed_generations": completed_generations,
            "active_promos": int(active_promos or 0),
            "total_promos": int(total_promos or 0),
            "active_products": int(active_products or 0),
            "total_products": int(total_products or 0),
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
