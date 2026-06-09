import re
import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import ShopProductType
from app.repositories.catalog_repository import CatalogRepository
from app.services.catalog_version_service import bump_catalog_version
from app.schemas.catalog import (
    AdminUserStatsResponse,
    HomeArtResponse,
    PromoCodeResponse,
    ShopProductResponse,
)


class CatalogService:
    def __init__(self, session: AsyncSession):
        self._repo = CatalogRepository(session)

    async def list_home_arts_public(self) -> list[HomeArtResponse]:
        items = await self._repo.list_home_arts(active_only=True)
        return [HomeArtResponse.model_validate(i) for i in items]

    async def user_stats(self) -> AdminUserStatsResponse:
        return AdminUserStatsResponse.model_validate(await self._repo.user_stats())

    async def list_home_arts(self) -> list[HomeArtResponse]:
        items = await self._repo.list_home_arts()
        return [HomeArtResponse.model_validate(i) for i in items]

    async def create_home_art(self, title: str, description: str, image_url: str | None = None) -> HomeArtResponse:
        item = await self._repo.create_home_art(title=title, description=description, image_url=image_url)
        return HomeArtResponse.model_validate(item)

    async def update_home_art(
        self,
        item_id: UUID,
        *,
        title: str | None = None,
        description: str | None = None,
        image_url: str | None = None,
    ) -> HomeArtResponse:
        item = await self._repo.get_home_art(item_id)
        if not item:
            raise NotFoundError("HomeArtItem", str(item_id))
        updated = await self._repo.update_home_art(
            item, title=title, description=description, image_url=image_url
        )
        return HomeArtResponse.model_validate(updated)

    async def delete_home_art(self, item_id: UUID) -> None:
        item = await self._repo.get_home_art(item_id)
        if not item:
            raise NotFoundError("HomeArtItem", str(item_id))
        await self._repo.delete_home_art(item)

    async def list_promos(self) -> list[PromoCodeResponse]:
        promos = await self._repo.list_promo_codes()
        return [PromoCodeResponse.model_validate(p) for p in promos]

    async def create_promo(
        self,
        name: str,
        discount_percent: int,
        code: str | None = None,
        *,
        max_uses: int | None = None,
        is_active: bool = True,
    ) -> PromoCodeResponse:
        if not 1 <= discount_percent <= 100:
            raise ValueError("discount_percent must be 1-100")
        normalized = (code or _slug_code(name)).upper()
        existing = await self._repo.get_promo_by_code(normalized)
        if existing:
            normalized = f"{normalized}{uuid.uuid4().hex[:4].upper()}"
        promo = await self._repo.create_promo(
            code=normalized,
            name=name,
            discount_percent=discount_percent,
            max_uses=max_uses,
            is_active=is_active,
        )
        return PromoCodeResponse.model_validate(promo)

    async def update_promo(self, promo_id: UUID, **kwargs) -> PromoCodeResponse:
        promo = await self._repo.get_promo(promo_id)
        if not promo:
            raise NotFoundError("PromoCode", str(promo_id))
        if "code" in kwargs and kwargs["code"]:
            kwargs["code"] = kwargs["code"].strip().upper()
        updated = await self._repo.update_promo(promo, **kwargs)
        return PromoCodeResponse.model_validate(updated)

    async def get_promo(self, promo_id: UUID) -> PromoCodeResponse:
        promo = await self._repo.get_promo(promo_id)
        if not promo:
            raise NotFoundError("PromoCode", str(promo_id))
        return PromoCodeResponse.model_validate(promo)

    async def delete_promo(self, promo_id: UUID) -> None:
        promo = await self._repo.get_promo(promo_id)
        if not promo:
            raise NotFoundError("PromoCode", str(promo_id))
        await self._repo.delete_promo(promo)

    async def list_products(self) -> list[ShopProductResponse]:
        products = await self._repo.list_products()
        return [ShopProductResponse.model_validate(p) for p in products]

    async def list_products_public(self) -> list[ShopProductResponse]:
        products = await self._repo.list_products(active_only=True)
        return [ShopProductResponse.model_validate(p) for p in products]

    async def create_product(
        self,
        name: str,
        product_type: ShopProductType,
        price: int,
        sale_price: int | None = None,
        gems_amount: int = 0,
        credits_amount: int = 0,
        *,
        is_active: bool = True,
        sort_order: int = 0,
        image_url: str | None = None,
    ) -> ShopProductResponse:
        product = await self._repo.create_product(
            name=name,
            product_type=product_type,
            price=price,
            sale_price=sale_price,
            gems_amount=gems_amount,
            credits_amount=credits_amount,
            is_active=is_active,
            sort_order=sort_order,
            image_url=image_url,
        )
        await bump_catalog_version()
        return ShopProductResponse.model_validate(product)

    async def get_product(self, product_id: UUID) -> ShopProductResponse:
        product = await self._repo.get_product(product_id)
        if not product:
            raise NotFoundError("ShopProduct", str(product_id))
        return ShopProductResponse.model_validate(product)

    async def update_product(self, product_id: UUID, **kwargs) -> ShopProductResponse:
        product = await self._repo.get_product(product_id)
        if not product:
            raise NotFoundError("ShopProduct", str(product_id))
        updated = await self._repo.update_product(product, **kwargs)
        await bump_catalog_version()
        return ShopProductResponse.model_validate(updated)

    async def delete_product(self, product_id: UUID) -> None:
        product = await self._repo.get_product(product_id)
        if not product:
            raise NotFoundError("ShopProduct", str(product_id))
        await self._repo.delete_product(product)
        await bump_catalog_version()


def _slug_code(name: str) -> str:
    base = re.sub(r"[^A-Za-z0-9]", "", name.upper())[:12]
    return base or "PROMO"
