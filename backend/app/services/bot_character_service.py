from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models import Character, CharacterScenario
from app.repositories.character_repository import CharacterRepository
from app.repositories.character_scenario_repository import CharacterScenarioRepository
from app.services.admin_service import AdminService
from app.utils.slugify import build_personality_prompt, slugify_name

DESCRIPTION_MAX_LEN = 500
BEHAVIOR_PARAMS_COUNT = 5


class BotCharacterService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._characters = CharacterRepository(session)
        self._scenarios = CharacterScenarioRepository(session)
        self._admin = AdminService(session)

    async def list_characters(self, page: int = 1, page_size: int = 50) -> tuple[list[Character], int]:
        """Active characters visible in catalog (excludes deleted/hidden)."""
        return await self._characters.list_active(page=page, page_size=page_size)

    async def list_catalog(self) -> list[Character]:
        return await self._characters.list_catalog_ordered()

    async def catalog_positions(self) -> dict[UUID, int]:
        catalog = await self.list_catalog()
        return {c.id: i + 1 for i, c in enumerate(catalog)}

    async def move_catalog_character(
        self,
        admin_id: UUID,
        character_id: UUID,
        direction: str,
    ) -> tuple[bool, int | None]:
        """Move character in home catalog. Returns (moved, new 1-based position)."""
        await self._admin.verify_admin(admin_id)
        character = await self.get_character(character_id)
        if not character.is_active or character.is_hidden:
            raise ValidationError("Персонаж не отображается в каталоге на главной")
        moved = await self._characters.move_catalog(character_id, direction)
        if not moved:
            return False, None
        positions = await self.catalog_positions()
        await self._admin._log(
            admin_id,
            "update",
            "character_order",
            str(character_id),
            {"direction": direction, "position": positions.get(character_id)},
        )
        return True, positions.get(character_id)

    async def get_character(self, character_id: UUID) -> Character:
        character = await self._characters.get_by_id(character_id)
        if not character:
            raise NotFoundError("Character", str(character_id))
        return character

    async def create_character(
        self,
        admin_id: UUID,
        *,
        name: str,
        description: str,
        subtitle: str,
        behavior_params: list[str],
        avatar_url: str | None = None,
        greeting_message: str = "",
    ) -> Character:
        await self._admin.verify_admin(admin_id)

        name = name.strip()
        if not name:
            raise ValidationError("Имя персонажа не может быть пустым")
        description = description.strip()
        if len(description) > DESCRIPTION_MAX_LEN:
            raise ValidationError(f"Описание не длиннее {DESCRIPTION_MAX_LEN} символов")
        if len(behavior_params) != BEHAVIOR_PARAMS_COUNT:
            raise ValidationError(f"Нужно ровно {BEHAVIOR_PARAMS_COUNT} параметров поведения")

        params = [p.strip() for p in behavior_params]
        personality = build_personality_prompt(params)

        character = await self._characters.create(
            name=name,
            slug=slugify_name(name),
            description=description,
            subtitle=subtitle.strip() or None,
            behavior_params=params,
            tags=params,
            personality_prompt=personality,
            greeting_message=greeting_message.strip(),
            avatar_url=avatar_url,
            preview_url=avatar_url,
            is_active=True,
            is_hidden=False,
            sort_order=0,
        )
        await self._characters.prepend_to_catalog(character.id)
        await self._admin._log(
            admin_id,
            "create",
            "character",
            str(character.id),
            {"name": name, "subtitle": subtitle},
        )
        return character

    async def list_scenarios(self, character_id: UUID) -> list[CharacterScenario]:
        await self.get_character(character_id)
        return await self._scenarios.list_for_character(character_id)

    async def create_scenario(
        self,
        admin_id: UUID,
        character_id: UUID,
        *,
        title: str,
        story: str,
        communication_style: str,
        opening_message: str = "",
    ) -> CharacterScenario:
        await self._admin.verify_admin(admin_id)
        await self.get_character(character_id)

        title = title.strip()
        if not title:
            raise ValidationError("Название сценария обязательно")

        count = await self._scenarios.count_for_character(character_id)
        scenario = await self._scenarios.create(
            character_id=character_id,
            title=title,
            story=story.strip(),
            communication_style=communication_style.strip(),
            opening_message=opening_message.strip(),
            sort_order=count,
        )
        await self._admin._log(
            admin_id,
            "create",
            "character_scenario",
            str(scenario.id),
            {"character_id": str(character_id), "title": title},
        )
        return scenario

    async def deactivate_scenario(self, admin_id: UUID, scenario_id: UUID) -> None:
        await self._admin.verify_admin(admin_id)
        scenario = await self._scenarios.get_by_id(scenario_id)
        if not scenario:
            raise NotFoundError("Scenario", str(scenario_id))
        await self._scenarios.deactivate(scenario)
        await self._admin._log(admin_id, "delete", "character_scenario", str(scenario_id))

    async def delete_character(self, admin_id: UUID, character_id: UUID) -> Character:
        await self._admin.verify_admin(admin_id)
        character = await self.get_character(character_id)
        if not character.is_active and character.is_hidden:
            raise ValidationError("Персонаж уже удалён")
        await self._characters.delete(character)
        await self._admin._log(
            admin_id,
            "delete",
            "character",
            str(character_id),
            {"name": character.name},
        )
        return character
