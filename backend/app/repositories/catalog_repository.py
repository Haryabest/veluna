from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import HomeArtItem, PromoCode, ShopProduct, ShopProductType, User


class CatalogRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    # --- Stats ---
    async def user_stats(self) -> dict:
        total = (await self._session.execute(select(func.count(User.id)))).scalar_one()
        active = (
            await self._session.execute(select(func.count(User.id)).where(User.is_active == True))  # noqa: E712
        ).scalar_one()
        banned = (
            await self._session.execute(select(func.count(User.id)).where(User.is_banned == True))  # noqa: E712
        ).scalar_one()
        return {"total": total, "active": active, "banned": banned}

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
