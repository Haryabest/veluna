from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Chat,
    Generation,
    HomeArtItem,
    Message,
    PromoCode,
    Purchase,
    PurchaseStatus,
    ShopProduct,
    ShopProductType,
    Transaction,
    TransactionType,
    User,
    UserBalance,
)


class CatalogRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    # --- Stats ---
    async def user_stats(self) -> dict:
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
        }

    # --- Home art ---
    async def list_home_arts(self, active_only: bool = False) -> list[HomeArtItem]:
        q = select(HomeArtItem).order_by(HomeArtItem.sort_order, HomeArtItem.title)
        if active_only:
            q = q.where(HomeArtItem.is_active == True)  # noqa: E712
        return list((await self._session.execute(q)).scalars().all())

    async def get_home_art(self, item_id: UUID) -> HomeArtItem | None:
        return (
            await self._session.execute(select(HomeArtItem).where(HomeArtItem.id == item_id))
        ).scalar_one_or_none()

    async def create_home_art(self, **kwargs) -> HomeArtItem:
        item = HomeArtItem(**kwargs)
        self._session.add(item)
        await self._session.flush()
        return item

    async def update_home_art(self, item: HomeArtItem, **kwargs) -> HomeArtItem:
        for k, v in kwargs.items():
            if v is not None and hasattr(item, k):
                setattr(item, k, v)
        await self._session.flush()
        return item

    async def delete_home_art(self, item: HomeArtItem) -> None:
        await self._session.delete(item)

    # --- Promo codes ---
    async def list_promo_codes(self) -> list[PromoCode]:
        result = await self._session.execute(
            select(PromoCode).order_by(PromoCode.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_promo(self, promo_id: UUID) -> PromoCode | None:
        return (
            await self._session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        ).scalar_one_or_none()

    async def get_promo_by_code(self, code: str) -> PromoCode | None:
        normalized = code.strip().upper()
        return (
            await self._session.execute(select(PromoCode).where(PromoCode.code == normalized))
        ).scalar_one_or_none()

    async def create_promo(self, **kwargs) -> PromoCode:
        promo = PromoCode(**kwargs)
        self._session.add(promo)
        await self._session.flush()
        return promo

    async def delete_promo(self, promo: PromoCode) -> None:
        await self._session.delete(promo)

    # --- Shop products ---
    async def list_products(self, active_only: bool = False) -> list[ShopProduct]:
        q = select(ShopProduct).order_by(ShopProduct.sort_order, ShopProduct.name)
        if active_only:
            q = q.where(ShopProduct.is_active == True)  # noqa: E712
        return list((await self._session.execute(q)).scalars().all())

    async def get_product(self, product_id: UUID) -> ShopProduct | None:
        return (
            await self._session.execute(select(ShopProduct).where(ShopProduct.id == product_id))
        ).scalar_one_or_none()

    async def create_product(self, **kwargs) -> ShopProduct:
        product = ShopProduct(**kwargs)
        self._session.add(product)
        await self._session.flush()
        return product

    async def update_product(self, product: ShopProduct, **kwargs) -> ShopProduct:
        for k, v in kwargs.items():
            if v is not None and hasattr(product, k):
                setattr(product, k, v)
        await self._session.flush()
        return product

    async def delete_product(self, product: ShopProduct) -> None:
        await self._session.delete(product)
