from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.character_repository import CharacterRepository
from app.schemas import (
    CharacterDetailResponse,
    CharacterResponse,
    PaginatedResponse,
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
