from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CharacterScenario


class CharacterScenarioRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, scenario_id: UUID) -> CharacterScenario | None:
        result = await self._session.execute(
            select(CharacterScenario).where(CharacterScenario.id == scenario_id)
        )
        return result.scalar_one_or_none()

    async def list_for_character(self, character_id: UUID) -> list[CharacterScenario]:
        result = await self._session.execute(
            select(CharacterScenario)
            .where(
                CharacterScenario.character_id == character_id,
                CharacterScenario.is_active == True,  # noqa: E712
            )
            .order_by(CharacterScenario.sort_order, CharacterScenario.created_at)
        )
        return list(result.scalars().all())

    async def count_for_character(self, character_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(CharacterScenario.id)).where(
                CharacterScenario.character_id == character_id,
                CharacterScenario.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one()

    async def create(self, **kwargs) -> CharacterScenario:
        scenario = CharacterScenario(**kwargs)
        self._session.add(scenario)
        await self._session.flush()
        return scenario

    async def update(self, scenario: CharacterScenario, **kwargs) -> CharacterScenario:
        for key, value in kwargs.items():
            if value is not None and hasattr(scenario, key):
                setattr(scenario, key, value)
        await self._session.flush()
        return scenario

    async def deactivate(self, scenario: CharacterScenario) -> None:
        scenario.is_active = False
        await self._session.flush()
