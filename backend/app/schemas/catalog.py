from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas import BaseSchema
from app.utils.media_url import normalize_media_url


class HomeArtResponse(BaseSchema):
    id: UUID
    title: str
    description: str
    image_url: str | None
    sort_order: int

    @field_validator("image_url", mode="before")
    @classmethod
    def _normalize_media(cls, v: str | None) -> str | None:
        return normalize_media_url(v)


class PromoCodeResponse(BaseSchema):
    id: UUID
    code: str
    name: str
    discount_percent: int
    is_active: bool
    max_uses: int | None = None
    used_count: int


class PromoCodeCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    discount_percent: int = Field(ge=1, le=100)
    code: str | None = Field(default=None, max_length=64)
    max_uses: int | None = Field(default=None, ge=1)
    is_active: bool = True


class PromoCodeUpdate(BaseSchema):
    name: str | None = Field(default=None, max_length=255)
    discount_percent: int | None = Field(default=None, ge=1, le=100)
    code: str | None = Field(default=None, max_length=64)
    max_uses: int | None = None
    is_active: bool | None = None


class ShopProductCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    product_type: Literal["gems", "credits", "bundle"]
    price: int = Field(ge=0)
    sale_price: int | None = Field(default=None, ge=0)
    gems_amount: int = Field(default=0, ge=0)
    credits_amount: int = Field(default=0, ge=0)
    is_active: bool = True
    sort_order: int = 0
    image_url: str | None = None


class ShopProductUpdate(BaseSchema):
    name: str | None = Field(default=None, max_length=255)
    price: int | None = Field(default=None, ge=0)
    sale_price: int | None = None
    gems_amount: int | None = Field(default=None, ge=0)
    credits_amount: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    sort_order: int | None = None
    image_url: str | None = None


class BroadcastRequest(BaseSchema):
    message: str = Field(min_length=1, max_length=4096)


class BroadcastResponse(BaseSchema):
    id: UUID
    status: str
    total_recipients: int
    sent_count: int
    failed_count: int
    message_text: str


class CatalogStatsResponse(BaseSchema):
    active_promos: int
    total_promos: int
    active_products: int
    total_products: int


class ShopProductResponse(BaseSchema):
    id: UUID
    name: str
    product_type: str
    price: int
    sale_price: int | None
    gems_amount: int
    credits_amount: int
    image_url: str | None = None
    is_active: bool

    @field_validator("image_url", mode="before")
    @classmethod
    def _normalize_media(cls, v: str | None) -> str | None:
        return normalize_media_url(v)


class AdminUserStatsResponse(BaseSchema):
    """Aggregated platform stats for Telegram admin."""

    total_users: int
    unique_users_ever: int
    active_users_24h: int
    active_users_7d: int
    banned_users: int
    payments_count: int
    payments_gems_total: int
    payments_stars_total: int
    revenue_gems_total: int
    expenses_gems_total: int
    usage_time_minutes: int
    avg_usage_minutes_per_user: float
    total_messages: int
    total_generations: int
    active_promos: int = 0
    total_promos: int = 0
    active_products: int = 0
    total_products: int = 0
