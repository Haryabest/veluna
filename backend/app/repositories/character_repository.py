from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Character


class CharacterRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, character_id: UUID) -> Character | None:
        result = await self._session.execute(select(Character).where(Character.id == character_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Character | None:
        result = await self._session.execute(select(Character).where(Character.slug == slug))
        return result.scalar_one_or_none()

    async def list_active(self, page: int = 1, page_size: int = 20, category: str | None = None) -> tuple[list[Character], int]:
        query = select(Character).where(Character.is_active == True, Character.is_hidden == False)  # noqa: E712
        if category:
            query = query.where(Character.category == category)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self._session.execute(count_query)).scalar_one()

        offset = (page - 1) * page_size
        result = await self._session.execute(
            query.order_by(Character.sort_order, Character.name).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def list_all(self, page: int = 1, page_size: int = 20) -> tuple[list[Character], int]:
        total = (await self._session.execute(select(func.count(Character.id)))).scalar_one()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(Character).order_by(Character.sort_order).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def create(self, **kwargs) -> Character:
        character = Character(**kwargs)
        self._session.add(character)
        await self._session.flush()
        return character

    async def update(self, character: Character, **kwargs) -> Character:
        for key, value in kwargs.items():
            if value is not None and hasattr(character, key):
                setattr(character, key, value)
        await self._session.flush()
        return character

    async def delete(self, character: Character) -> None:
        character.is_active = False
        character.is_hidden = True
        await self._session.flush()
