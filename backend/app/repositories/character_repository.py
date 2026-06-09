from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Character

_CATALOG_VISIBLE = (Character.is_active == True, Character.is_hidden == False)  # noqa: E712


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
            if hasattr(character, key):
                setattr(character, key, value)
        await self._session.flush()
        return character

    async def delete(self, character: Character) -> None:
        character.is_active = False
        character.is_hidden = True
        await self._session.flush()

    async def list_catalog_ordered(self) -> list[Character]:
        result = await self._session.execute(
            select(Character)
            .where(*_CATALOG_VISIBLE)
            .order_by(Character.sort_order, Character.name)
        )
        return list(result.scalars().all())

    async def bump_catalog_sort_orders(self) -> None:
        await self._session.execute(
            update(Character)
            .where(*_CATALOG_VISIBLE)
            .values(sort_order=Character.sort_order + 1)
        )

    async def prepend_to_catalog(self, character_id: UUID) -> None:
        await self.bump_catalog_sort_orders()
        character = await self.get_by_id(character_id)
        if character:
            character.sort_order = 0
            await self._session.flush()

    async def move_catalog(self, character_id: UUID, direction: str) -> bool:
        catalog = await self.list_catalog_ordered()
        idx = next((i for i, c in enumerate(catalog) if c.id == character_id), None)
        if idx is None:
            return False
        if direction == "up" and idx > 0:
            catalog[idx], catalog[idx - 1] = catalog[idx - 1], catalog[idx]
        elif direction == "down" and idx < len(catalog) - 1:
            catalog[idx], catalog[idx + 1] = catalog[idx + 1], catalog[idx]
        elif direction == "top" and idx > 0:
            item = catalog.pop(idx)
            catalog.insert(0, item)
        else:
            return False
        for i, character in enumerate(catalog):
            character.sort_order = i
        await self._session.flush()
        return True
