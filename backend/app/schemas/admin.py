from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas import BaseSchema, CharacterDetailResponse, TransactionResponse, UserResponse


class GemAdjustRequest(BaseSchema):
    amount: int = Field(description="Positive to add, negative to deduct")
    description: str = "Admin adjustment"


class UserBanRequest(BaseSchema):
    is_banned: bool
    reason: str | None = Field(default=None, max_length=2000)
    duration_days: int | None = Field(
        default=None,
        ge=1,
        le=3650,
        description="None = permanent ban",
    )


class AdminStatsResponse(BaseSchema):
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
    total_revenue_gems: int
    pending_generations: int
    completed_generations: int
    active_promos: int = 0
    total_promos: int = 0
    active_products: int = 0
    total_products: int = 0


class AdminLogResponse(BaseSchema):
    id: UUID
    admin_id: UUID
    action: str
    resource_type: str
    resource_id: str | None
    details: dict
    created_at: datetime


class AnalyticsSummaryResponse(BaseSchema):
    event_type: str
    count: int


class ApiUsageResponse(BaseSchema):
    chat_provider: str
    image_provider: str
    total_generations: int
    completed_generations: int
    failed_generations: int
    total_chat_tokens: int


class PricingConfigResponse(BaseSchema):
    gem_cost_per_message: int
    gem_cost_per_generation: int
    default_user_gems: int


class PricingConfigUpdate(BaseSchema):
    gem_cost_per_message: int | None = Field(default=None, ge=0)
    gem_cost_per_generation: int | None = Field(default=None, ge=0)
    default_user_gems: int | None = Field(default=None, ge=0)


class CharacterMediaUploadRequest(BaseSchema):
    media_type: Literal["avatar", "preview"]
    content_type: str = "image/jpeg"
    file_extension: str = "jpg"


class CharacterMediaUploadResponse(BaseSchema):
    upload_url: str
    public_url: str
    storage_key: str
    expires_in: int


class CharacterMediaConfirmRequest(BaseSchema):
    media_type: Literal["avatar", "preview"]
    public_url: str


class AdminUserDetailResponse(UserResponse):
    is_banned: bool
    ban_reason: str | None = None
    banned_until: datetime | None = None
    last_seen_at: datetime | None
    credits: int = 0
    total_spent: int = 0
    total_earned: int = 0


class AdminUserStatsDetailResponse(BaseSchema):
    user_id: UUID
    chats_count: int = 0
    messages_count: int = 0
    generations_total: int = 0
    generations_completed: int = 0
    purchases_completed: int = 0
    stars_spent_total: int = 0
    gems_purchased_total: int = 0
    gems_spent_total: int = 0
    credits: int = 0
    total_earned: int = 0
    registered_at: datetime
    last_seen_at: datetime | None
    last_chat_at: datetime | None


class AdminUserUpdateRequest(BaseSchema):
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    language_code: str | None = Field(default=None, max_length=10)
    role: Literal["user", "admin"] | None = None
    is_active: bool | None = None
    is_banned: bool | None = None
    gems: int | None = Field(default=None, ge=0)
    credits: int | None = Field(default=None, ge=0)
