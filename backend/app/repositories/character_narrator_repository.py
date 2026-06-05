from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CharacterNarrator


class CharacterNarratorRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, narrator_id: UUID) -> CharacterNarrator | None:
        result = await self._session.execute(
            select(CharacterNarrator).where(CharacterNarrator.id == narrator_id)
        )
        return result.scalar_one_or_none()

    async def list_for_character(self, character_id: UUID) -> list[CharacterNarrator]:
        result = await self._session.execute(
            select(CharacterNarrator)
            .where(
                CharacterNarrator.character_id == character_id,
                CharacterNarrator.is_active == True,  # noqa: E712
            )
            .order_by(CharacterNarrator.sort_order, CharacterNarrator.created_at)
        )
        return list(result.scalars().all())

    async def count_for_character(self, character_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(CharacterNarrator.id)).where(
                CharacterNarrator.character_id == character_id,
                CharacterNarrator.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one()

    async def create(self, **kwargs) -> CharacterNarrator:
        narrator = CharacterNarrator(**kwargs)
        self._session.add(narrator)
        await self._session.flush()
        return narrator

    async def update(self, narrator: CharacterNarrator, **kwargs) -> CharacterNarrator:
        for key, value in kwargs.items():
            if value is not None and hasattr(narrator, key):
                setattr(narrator, key, value)
        await self._session.flush()
        return narrator

    async def deactivate(self, narrator: CharacterNarrator) -> None:
        narrator.is_active = False
        await self._session.flush()
