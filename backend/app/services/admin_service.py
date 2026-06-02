import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.providers.factory import get_storage_provider
from app.providers.storage.base import StorageBucket
from app.repositories.admin_repository import AdminRepository
from app.repositories.character_repository import CharacterRepository
from app.repositories.generation_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.schemas import (
    CharacterCreate,
    CharacterDetailResponse,
    CharacterUpdate,
    PaginatedResponse,
    TransactionResponse,
    UserResponse,
)
from app.schemas.admin import (
    AdminLogResponse,
    AdminStatsResponse,
    AdminUserDetailResponse,
    AnalyticsSummaryResponse,
    ApiUsageResponse,
    CharacterMediaConfirmRequest,
    CharacterMediaUploadRequest,
    CharacterMediaUploadResponse,
    PricingConfigResponse,
    PricingConfigUpdate,
)
from app.services.platform_settings_service import PlatformSettingsService


class AdminService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._users = UserRepository(session)
        self._characters = CharacterRepository(session)
        self._payments = PaymentRepository(session)
        self._admin = AdminRepository(session)
        self._settings = get_settings()
        self._platform = PlatformSettingsService(self._settings)

    async def verify_admin(self, user_id: UUID) -> None:
        user = await self._users.get_by_id(user_id)
        if not user or not await self._users.is_admin(user):
            raise ForbiddenError("Admin access required")

    async def _log(
        self,
        admin_id: UUID,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        await self._admin.log_action(admin_id, action, resource_type, resource_id, details)

    def _user_response(self, user) -> UserResponse:
        return UserResponse(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            photo_url=user.photo_url,
            language_code=user.language_code,
            role=user.role.value,
            is_active=user.is_active,
            gems=user.balance.gems if user.balance else 0,
            created_at=user.created_at,
        )

    async def get_stats(self, admin_id: UUID) -> AdminStatsResponse:
        await self.verify_admin(admin_id)
        return AdminStatsResponse(**(await self._admin.get_stats()))

    async def list_users(self, admin_id: UUID, page: int = 1) -> PaginatedResponse:
        await self.verify_admin(admin_id)
        users, total = await self._users.list_paginated(page=page)
        page_size = 20
        return PaginatedResponse(
            items=[self._user_response(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size or 1,
        )

    async def get_user(self, admin_id: UUID, user_id: UUID) -> AdminUserDetailResponse:
        await self.verify_admin(admin_id)
        user = await self._users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        balance = user.balance
        base = self._user_response(user)
        return AdminUserDetailResponse(
            **base.model_dump(),
            is_banned=user.is_banned,
            last_seen_at=user.last_seen_at,
            total_spent=balance.total_spent if balance else 0,
            total_earned=balance.total_earned if balance else 0,
        )

    async def set_user_ban(self, admin_id: UUID, user_id: UUID, is_banned: bool) -> AdminUserDetailResponse:
        await self.verify_admin(admin_id)
        user = await self._users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        await self._users.update(user, is_banned=is_banned)
        await self._log(admin_id, "ban" if is_banned else "unban", "user", str(user_id))
        return await self.get_user(admin_id, user_id)

    async def adjust_gems(self, admin_id: UUID, user_id: UUID, amount: int, description: str) -> None:
        await self.verify_admin(admin_id)
        from app.models import TransactionType

        if amount > 0:
            await self._payments.add_gems(user_id, amount, TransactionType.ADMIN_ADJUST, description)
        else:
            await self._payments.deduct_gems(user_id, abs(amount), description)
        await self._log(
            admin_id,
            "adjust_gems",
            "user",
            str(user_id),
            {"amount": amount, "description": description},
        )

    async def list_characters(self, admin_id: UUID, page: int = 1) -> PaginatedResponse:
        await self.verify_admin(admin_id)
        characters, total = await self._characters.list_all(page=page)
        page_size = 20
        return PaginatedResponse(
            items=[CharacterDetailResponse.model_validate(c) for c in characters],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size or 1,
        )

    async def get_character(self, admin_id: UUID, character_id: UUID) -> CharacterDetailResponse:
        await self.verify_admin(admin_id)
        character = await self._characters.get_by_id(character_id)
        if not character:
            raise NotFoundError("Character", str(character_id))
        return CharacterDetailResponse.model_validate(character)

    async def create_character(self, admin_id: UUID, data: CharacterCreate) -> CharacterDetailResponse:
        await self.verify_admin(admin_id)
        character = await self._characters.create(**data.model_dump())
        await self._log(admin_id, "create", "character", str(character.id), data.model_dump())
        return CharacterDetailResponse.model_validate(character)

    async def update_character(
        self, admin_id: UUID, character_id: UUID, data: CharacterUpdate
    ) -> CharacterDetailResponse:
        await self.verify_admin(admin_id)
        character = await self._characters.get_by_id(character_id)
        if not character:
            raise NotFoundError("Character", str(character_id))
        updated = await self._characters.update(character, **data.model_dump(exclude_unset=True))
        await self._log(
            admin_id,
            "update",
            "character",
            str(character_id),
            data.model_dump(exclude_unset=True),
        )
        return CharacterDetailResponse.model_validate(updated)

    async def delete_character(self, admin_id: UUID, character_id: UUID) -> None:
        await self.verify_admin(admin_id)
        character = await self._characters.get_by_id(character_id)
        if not character:
            raise NotFoundError("Character", str(character_id))
        await self._characters.delete(character)
        await self._log(admin_id, "delete", "character", str(character_id))

    async def request_media_upload(
        self,
        admin_id: UUID,
        character_id: UUID,
        payload: CharacterMediaUploadRequest,
    ) -> CharacterMediaUploadResponse:
        await self.verify_admin(admin_id)
        character = await self._characters.get_by_id(character_id)
        if not character:
            raise NotFoundError("Character", str(character_id))

        storage = get_storage_provider()
        object_key = f"{character.slug}/{payload.media_type}-{uuid.uuid4().hex[:8]}.{payload.file_extension}"
        result = await storage.get_presigned_upload_url(
            StorageBucket.CHARACTERS,
            object_key,
            content_type=payload.content_type,
            expires=3600,
        )
        public_url = result.public_url or await storage.get_public_url(StorageBucket.CHARACTERS, object_key)
        await self._log(
            admin_id,
            "media_upload_url",
            "character",
            str(character_id),
            {"media_type": payload.media_type, "key": result.key},
        )
        return CharacterMediaUploadResponse(
            upload_url=result.url,
            public_url=public_url,
            storage_key=result.key or object_key,
            expires_in=result.expires_in,
        )

    async def confirm_media(
        self,
        admin_id: UUID,
        character_id: UUID,
        payload: CharacterMediaConfirmRequest,
    ) -> CharacterDetailResponse:
        await self.verify_admin(admin_id)
        character = await self._characters.get_by_id(character_id)
        if not character:
            raise NotFoundError("Character", str(character_id))

        field = "avatar_url" if payload.media_type == "avatar" else "preview_url"
        updated = await self._characters.update(character, **{field: payload.public_url})
        await self._log(
            admin_id,
            "media_confirm",
            "character",
            str(character_id),
            {"media_type": payload.media_type, "url": payload.public_url},
        )
        return CharacterDetailResponse.model_validate(updated)

    async def list_transactions(self, admin_id: UUID, page: int = 1) -> PaginatedResponse:
        await self.verify_admin(admin_id)
        txs, total = await self._admin.list_transactions(page=page)
        page_size = 20
        return PaginatedResponse(
            items=[
                TransactionResponse(
                    id=t.id,
                    type=t.type.value,
                    amount=t.amount,
                    balance_after=t.balance_after,
                    description=t.description,
                    created_at=t.created_at,
                )
                for t in txs
            ],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size or 1,
        )

    async def list_logs(self, admin_id: UUID, page: int = 1) -> PaginatedResponse:
        await self.verify_admin(admin_id)
        logs, total = await self._admin.list_logs(page=page)
        page_size = 20
        return PaginatedResponse(
            items=[AdminLogResponse.model_validate(log) for log in logs],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size or 1,
        )

    async def analytics_summary(self, admin_id: UUID, days: int = 7) -> list[AnalyticsSummaryResponse]:
        await self.verify_admin(admin_id)
        rows = await self._admin.analytics_summary(days=days)
        return [AnalyticsSummaryResponse(event_type=event_type, count=count) for event_type, count in rows]

    async def api_usage(self, admin_id: UUID) -> ApiUsageResponse:
        await self.verify_admin(admin_id)
        status_counts = await self._admin.generation_status_counts()
        total = sum(status_counts.values())
        return ApiUsageResponse(
            chat_provider=self._settings.ai_chat_provider,
            image_provider=self._settings.image_provider,
            total_generations=total,
            completed_generations=status_counts.get("completed", 0),
            failed_generations=status_counts.get("failed", 0),
            total_chat_tokens=await self._admin.total_chat_tokens(),
        )

    async def get_pricing(self, admin_id: UUID) -> PricingConfigResponse:
        await self.verify_admin(admin_id)
        return await self._platform.get_pricing()

    async def update_pricing(self, admin_id: UUID, data: PricingConfigUpdate) -> PricingConfigResponse:
        await self.verify_admin(admin_id)
        updated = await self._platform.update_pricing(data)
        await self._log(admin_id, "update_pricing", "platform", None, updated.model_dump())
        return updated
