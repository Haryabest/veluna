from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.character_narrator_repository import CharacterNarratorRepository
from app.repositories.character_repository import CharacterRepository
from app.repositories.character_scenario_repository import CharacterScenarioRepository
from app.schemas import PaginatedResponse
from app.utils.locale import AppLocale
from app.utils.response_localization import (
    character_detail_response,
    character_response,
    narrator_response,
    request_locale,
    scenario_response,
)


class CharacterService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._characters = CharacterRepository(session)
        self._scenarios = CharacterScenarioRepository(session)
        self._narrators = CharacterNarratorRepository(session)

    async def list_characters(
        self, page: int = 1, category: str | None = None, *, locale: str | AppLocale = "ru"
    ) -> PaginatedResponse:
        characters, total = await self._characters.list_active(page=page, category=category)
        loc = request_locale(locale)
        page_size = 20
        return PaginatedResponse(
            items=[character_response(c, loc) for c in characters],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )

    async def get_character(self, character_id: UUID, *, locale: str | AppLocale = "ru"):
        character = await self._characters.get_by_id(character_id)
        if not character or not character.is_active:
            raise NotFoundError("Character", str(character_id))
        return character_detail_response(character, request_locale(locale))

    async def get_by_slug(self, slug: str, *, locale: str | AppLocale = "ru"):
        character = await self._characters.get_by_slug(slug)
        if not character or not character.is_active:
            raise NotFoundError("Character", slug)
        return character_detail_response(character, request_locale(locale))

    async def list_scenarios(self, character_id: UUID, *, locale: str | AppLocale = "ru"):
        character = await self._characters.get_by_id(character_id)
        if not character or not character.is_active:
            raise NotFoundError("Character", str(character_id))
        scenarios = await self._scenarios.list_for_character(character_id)
        loc = request_locale(locale)
        return [scenario_response(s, loc) for s in scenarios]

    async def list_narrators(self, character_id: UUID, *, locale: str | AppLocale = "ru"):
        character = await self._characters.get_by_id(character_id)
        if not character or not character.is_active:
            raise NotFoundError("Character", str(character_id))
        narrators = await self._narrators.list_for_character(character_id)
        loc = request_locale(locale)
        return [narrator_response(n, loc) for n in narrators]
