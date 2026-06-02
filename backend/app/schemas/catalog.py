from uuid import UUID

from app.schemas import BaseSchema


class HomeArtResponse(BaseSchema):
    id: UUID
    title: str
    description: str
    image_url: str | None
    sort_order: int


class PromoCodeResponse(BaseSchema):
    id: UUID
    code: str
    name: str
    discount_percent: int
    is_active: bool
    used_count: int


class ShopProductResponse(BaseSchema):
    id: UUID
    name: str
    product_type: str
    price: int
    sale_price: int | None
    gems_amount: int
    credits_amount: int
    is_active: bool


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
