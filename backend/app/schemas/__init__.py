from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.media_url import normalize_media_url


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TelegramAuthRequest(BaseSchema):
    init_data: str


class UserResponse(BaseSchema):
    id: UUID
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    language_code: str
    role: str
    is_active: bool
    gems: int = 0
    created_at: datetime


class UserBalanceResponse(BaseSchema):
    gems: int
    total_spent: int
    total_earned: int


class CharacterCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: str = ""
    personality_prompt: str = ""
    greeting_message: str = ""
    tags: list[str] = []
    category: str = "general"
    message_price: int = 1
    generation_price: int = 10
    is_nsfw: bool = False
    sort_order: int = 0


class CharacterUpdate(BaseSchema):
    name: str | None = None
    description: str | None = None
    personality_prompt: str | None = None
    greeting_message: str | None = None
    tags: list[str] | None = None
    category: str | None = None
    message_price: int | None = None
    generation_price: int | None = None
    is_active: bool | None = None
    is_hidden: bool | None = None
    is_nsfw: bool | None = None
    sort_order: int | None = None


class CharacterResponse(BaseSchema):
    id: UUID
    name: str
    slug: str
    subtitle: str | None = None
    description: str
    greeting_message: str
    avatar_url: str | None
    preview_url: str | None
    tags: list
    category: str
    message_price: int
    generation_price: int
    is_nsfw: bool
    sort_order: int

    @field_validator("avatar_url", "preview_url", mode="before")
    @classmethod
    def _normalize_media(cls, v: str | None) -> str | None:
        return normalize_media_url(v)


class CharacterDetailResponse(CharacterResponse):
    personality_prompt: str
    behavior_params: list[str] = []


class CharacterScenarioResponse(BaseSchema):
    id: UUID
    character_id: UUID
    title: str
    story: str
    communication_style: str
    opening_message: str
    sort_order: int


class CharacterNarratorResponse(BaseSchema):
    id: UUID
    character_id: UUID
    name: str
    description: str
    price: int
    sort_order: int


class ChatCreate(BaseSchema):
    character_id: UUID
    scenario_id: UUID
    narrator_id: UUID


class ChatScenarioUpdate(BaseSchema):
    scenario_id: UUID


class ChatNarratorUpdate(BaseSchema):
    narrator_id: UUID


class ChatResponse(BaseSchema):
    id: UUID
    character_id: UUID
    scenario_id: UUID | None = None
    narrator_id: UUID | None = None
    character_name: str = ""
    scenario_title: str | None = None
    narrator_name: str | None = None
    character_avatar_url: str | None = None
    status: str
    message_count: int
    last_message_at: datetime | None
    ai_reply_status: str = "idle"
    ai_reply_error: str | None = None
    created_at: datetime

    @field_validator("character_avatar_url", mode="before")
    @classmethod
    def _normalize_chat_avatar(cls, v: str | None) -> str | None:
        return normalize_media_url(v)


class ChatListResponse(BaseSchema):
    id: UUID
    character_id: UUID
    scenario_id: UUID | None = None
    scenario_title: str | None = None
    narrator_id: UUID | None = None
    narrator_name: str | None = None
    character_name: str
    character_avatar_url: str | None = None
    display_title: str
    is_pinned: bool = False
    is_system: bool = False
    last_message_preview: str | None = None
    last_message_at: datetime | None = None
    message_count: int = 0
    unread: int = 0

    @field_validator("character_avatar_url", mode="before")
    @classmethod
    def _normalize_media(cls, v: str | None) -> str | None:
        return normalize_media_url(v)


class ChatUpdate(BaseSchema):
    title: str = Field(min_length=1, max_length=64)


class ChatPinUpdate(BaseSchema):
    pinned: bool


class MessageCreate(BaseSchema):
    content: str = Field(min_length=1, max_length=4000)
    reply_to_id: UUID | None = None


class MessageReplyPreview(BaseSchema):
    id: UUID
    role: str
    content: str


class MessageResponse(BaseSchema):
    id: UUID
    chat_id: UUID
    role: str
    content: str
    tokens_used: int
    is_regenerated: bool
    reply_to_id: UUID | None = None
    reply_preview: MessageReplyPreview | None = None
    created_at: datetime


class SendMessageResponse(BaseSchema):
    user_message: MessageResponse
    ai_reply_status: str = "processing"


class MessageDeleteResponse(BaseSchema):
    id: UUID
    deleted: bool = True
    scope: str


class GenerationCreate(BaseSchema):
    prompt: str = Field(min_length=1, max_length=2000)
    negative_prompt: str = ""
    character_id: UUID | None = None
    model_id: str | None = None
    width: int = 512
    height: int = 768


class GenerationResponse(BaseSchema):
    id: UUID
    prompt: str
    status: str
    image_url: str | None
    thumbnail_url: str | None
    error_message: str | None
    gems_cost: int
    created_at: datetime

    @field_validator("image_url", "thumbnail_url", mode="before")
    @classmethod
    def _normalize_media(cls, v: str | None) -> str | None:
        return normalize_media_url(v)


class PurchaseCreate(BaseSchema):
    gems_amount: int = Field(gt=0)
    stars_amount: int = Field(gt=0)


class TransactionResponse(BaseSchema):
    id: UUID
    type: str
    amount: int
    balance_after: int
    description: str
    metadata: dict = Field(default_factory=dict, validation_alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class AdminStatsResponse(BaseSchema):
    total_users: int
    active_users_24h: int
    total_messages: int
    total_generations: int
    total_revenue_gems: int


class PaginatedResponse(BaseSchema):
    items: list
    total: int
    page: int
    page_size: int
    pages: int
