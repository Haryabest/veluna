from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.repositories.character_repository import CharacterRepository
from app.repositories.generation_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.schemas import (
    CharacterCreate,
    CharacterDetailResponse,
    CharacterResponse,
    CharacterUpdate,
    PaginatedResponse,
    UserResponse,
)


class CharacterService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._characters = CharacterRepository(session)

    async def list_characters(self, page: int = 1, category: str | None = None) -> PaginatedResponse:
        characters, total = await self._characters.list_active(page=page, category=category)
        page_size = 20
        return PaginatedResponse(
            items=[CharacterResponse.model_validate(c) for c in characters],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )

    async def get_character(self, character_id: UUID) -> CharacterDetailResponse:
        character = await self._characters.get_by_id(character_id)
        if not character or not character.is_active:
            raise NotFoundError("Character", str(character_id))
        return CharacterDetailResponse.model_validate(character)

    async def get_by_slug(self, slug: str) -> CharacterDetailResponse:
        character = await self._characters.get_by_slug(slug)
        if not character or not character.is_active:
            raise NotFoundError("Character", slug)
        return CharacterDetailResponse.model_validate(character)


class AdminService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._users = UserRepository(session)
        self._characters = CharacterRepository(session)
        self._payments = PaymentRepository(session)

    async def verify_admin(self, user_id: UUID) -> None:
        user = await self._users.get_by_id(user_id)
        if not user or not await self._users.is_admin(user):
            raise ForbiddenError("Admin access required")

    async def create_character(self, admin_id: UUID, data: CharacterCreate) -> CharacterDetailResponse:
        await self.verify_admin(admin_id)
        character = await self._characters.create(**data.model_dump())
        return CharacterDetailResponse.model_validate(character)

    async def update_character(self, admin_id: UUID, character_id: UUID, data: CharacterUpdate) -> CharacterDetailResponse:
        await self.verify_admin(admin_id)
        character = await self._characters.get_by_id(character_id)
        if not character:
            raise NotFoundError("Character", str(character_id))
        updated = await self._characters.update(character, **data.model_dump(exclude_unset=True))
        return CharacterDetailResponse.model_validate(updated)

    async def list_users(self, admin_id: UUID, page: int = 1) -> PaginatedResponse:
        await self.verify_admin(admin_id)
        users, total = await self._users.list_paginated(page=page)
        page_size = 20
        items = []
        for u in users:
            items.append(UserResponse(
                id=u.id,
                telegram_id=u.telegram_id,
                username=u.username,
                first_name=u.first_name,
                last_name=u.last_name,
                photo_url=u.photo_url,
                language_code=u.language_code,
                role=u.role.value,
                is_active=u.is_active,
                gems=u.balance.gems if u.balance else 0,
                created_at=u.created_at,
            ))
        return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=(total + page_size - 1) // page_size)

    async def adjust_gems(self, admin_id: UUID, user_id: UUID, amount: int, description: str) -> None:
        await self.verify_admin(admin_id)
        from app.models import TransactionType
        if amount > 0:
            await self._payments.add_gems(user_id, amount, TransactionType.ADMIN_ADJUST, description)
        else:
            await self._payments.deduct_gems(user_id, abs(amount), description)
