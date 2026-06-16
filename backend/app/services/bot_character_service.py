from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models import Character, CharacterNarrator, CharacterScenario
from app.repositories.character_narrator_repository import CharacterNarratorRepository
from app.repositories.character_repository import CharacterRepository
from app.repositories.character_scenario_repository import CharacterScenarioRepository
from app.services.admin_service import AdminService
from app.services.catalog_version_service import bump_catalog_version
from app.utils.slugify import build_personality_prompt, slugify_name

DESCRIPTION_MAX_LEN = 500
BEHAVIOR_PARAMS_COUNT = 5


class BotCharacterService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._characters = CharacterRepository(session)
        self._scenarios = CharacterScenarioRepository(session)
        self._narrators = CharacterNarratorRepository(session)
        self._admin = AdminService(session)

    @staticmethod
    async def _touch_catalog() -> None:
        await bump_catalog_version()

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
        if moved:
            await self._touch_catalog()
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
        name_en: str | None = None,
        description: str,
        description_en: str | None = None,
        subtitle: str,
        subtitle_en: str | None = None,
        behavior_params: list[str],
        avatar_url: str | None = None,
        greeting_message: str = "",
    ) -> Character:
        await self._admin.verify_admin(admin_id)

        name = name.strip()
        if not name:
            raise ValidationError("Имя персонажа не может быть пустым")
        name_en = name_en.strip() if name_en else None
        description = description.strip()
        description_en = description_en.strip() if description_en else None
        if len(description) > DESCRIPTION_MAX_LEN:
            raise ValidationError(f"Описание не длиннее {DESCRIPTION_MAX_LEN} символов")
        if description_en and len(description_en) > DESCRIPTION_MAX_LEN:
            raise ValidationError(f"Английское описание не длиннее {DESCRIPTION_MAX_LEN} символов")
        if len(behavior_params) != BEHAVIOR_PARAMS_COUNT:
            raise ValidationError(f"Нужно ровно {BEHAVIOR_PARAMS_COUNT} параметров поведения")

        params = [p.strip() for p in behavior_params]
        personality = build_personality_prompt(params)

        character = await self._characters.create(
            name=name,
            name_en=name_en,
            slug=slugify_name(name),
            description=description,
            description_en=description_en,
            subtitle=subtitle.strip() or None,
            subtitle_en=subtitle_en.strip() if subtitle_en else None,
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
        await self._touch_catalog()
        return character

    async def update_character(
        self,
        admin_id: UUID,
        character_id: UUID,
        *,
        name: str | None = None,
        name_en: str | None = None,
        description: str | None = None,
        description_en: str | None = None,
        subtitle: str | None = None,
        subtitle_en: str | None = None,
        behavior_params: list[str] | None = None,
        avatar_url: str | None = None,
        clear_avatar: bool = False,
    ) -> Character:
        await self._admin.verify_admin(admin_id)
        character = await self.get_character(character_id)

        updates: dict = {}
        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationError("Имя персонажа не может быть пустым")
            updates["name"] = name
        if name_en is not None:
            updates["name_en"] = name_en.strip() or None
        if description is not None:
            description = description.strip()
            if not description:
                raise ValidationError("Описание не может быть пустым")
            if len(description) > DESCRIPTION_MAX_LEN:
                raise ValidationError(f"Описание не длиннее {DESCRIPTION_MAX_LEN} символов")
            updates["description"] = description
        if description_en is not None:
            description_en = description_en.strip()
            if description_en and len(description_en) > DESCRIPTION_MAX_LEN:
                raise ValidationError(f"Английское описание не длиннее {DESCRIPTION_MAX_LEN} символов")
            updates["description_en"] = description_en or None
        if subtitle is not None:
            updates["subtitle"] = subtitle.strip() or None
        if subtitle_en is not None:
            updates["subtitle_en"] = subtitle_en.strip() or None
        if behavior_params is not None:
            if len(behavior_params) != BEHAVIOR_PARAMS_COUNT:
                raise ValidationError(f"Нужно ровно {BEHAVIOR_PARAMS_COUNT} параметров поведения")
            params = [p.strip() for p in behavior_params]
            if any(not p for p in params):
                raise ValidationError("Параметры поведения не могут быть пустыми")
            personality = build_personality_prompt(params)
            updates["behavior_params"] = params
            updates["tags"] = params
            updates["personality_prompt"] = personality
        if clear_avatar:
            updates["avatar_url"] = None
            updates["preview_url"] = None
        elif avatar_url is not None:
            updates["avatar_url"] = avatar_url
            updates["preview_url"] = avatar_url

        if updates:
            await self._characters.update(character, **updates)
            await self._admin._log(
                admin_id,
                "update",
                "character",
                str(character_id),
                {k: v for k, v in updates.items() if k != "personality_prompt"},
            )
            await self._touch_catalog()
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
        title_en: str | None = None,
        story: str,
        story_en: str | None = None,
        communication_style: str,
        communication_style_en: str | None = None,
        opening_message: str = "",
        opening_message_en: str | None = None,
    ) -> CharacterScenario:
        await self._admin.verify_admin(admin_id)
        await self.get_character(character_id)

        title = title.strip()
        if not title:
            raise ValidationError("Название сценария обязательно")
        title_en = title_en.strip() if title_en else None

        count = await self._scenarios.count_for_character(character_id)
        scenario = await self._scenarios.create(
            character_id=character_id,
            title=title,
            title_en=title_en,
            story=story.strip(),
            story_en=story_en.strip() if story_en else None,
            communication_style=communication_style.strip(),
            communication_style_en=communication_style_en.strip() if communication_style_en else None,
            opening_message=opening_message.strip(),
            opening_message_en=opening_message_en.strip() if opening_message_en else None,
            sort_order=count,
        )
        await self._admin._log(
            admin_id,
            "create",
            "character_scenario",
            str(scenario.id),
            {"character_id": str(character_id), "title": title},
        )
        await self._touch_catalog()
        return scenario
        await self._admin.verify_admin(admin_id)
        scenario = await self._scenarios.get_by_id(scenario_id)
        if not scenario:
            raise NotFoundError("Scenario", str(scenario_id))
        await self._scenarios.deactivate(scenario)
        await self._admin._log(admin_id, "delete", "character_scenario", str(scenario_id))
        await self._touch_catalog()

    async def list_narrators(self, character_id: UUID) -> list[CharacterNarrator]:
        await self.get_character(character_id)
        return await self._narrators.list_for_character(character_id)

    async def create_narrator(
        self,
        admin_id: UUID,
        character_id: UUID,
        *,
        name: str,
        name_en: str | None = None,
        description: str,
        description_en: str | None = None,
        price: int = 0,
    ) -> CharacterNarrator:
        await self._admin.verify_admin(admin_id)
        await self.get_character(character_id)

        name = name.strip()
        if not name:
            raise ValidationError("Название рассказчика обязательно")
        name_en = name_en.strip() if name_en else None

        count = await self._narrators.count_for_character(character_id)
        narrator = await self._narrators.create(
            character_id=character_id,
            name=name,
            name_en=name_en,
            description=description.strip(),
            description_en=description_en.strip() if description_en else None,
            price=max(0, price),
            sort_order=count,
        )
        await self._admin._log(
            admin_id,
            "create",
            "character_narrator",
            str(narrator.id),
            {"character_id": str(character_id), "name": name},
        )
        await self._touch_catalog()
        return narrator

    async def update_narrator(
        self,
        admin_id: UUID,
        narrator_id: UUID,
        *,
        price: int | None = None,
        image_url: str | None = None,
        clear_image: bool = False,
    ) -> CharacterNarrator:
        await self._admin.verify_admin(admin_id)
        narrator = await self._narrators.get_by_id(narrator_id)
        if not narrator:
            raise NotFoundError("Narrator", str(narrator_id))
        updates: dict = {}
        if price is not None:
            updates["price"] = max(0, price)
        if clear_image:
            updates["image_url"] = None
        elif image_url is not None:
            updates["image_url"] = image_url
        if updates:
            await self._narrators.update(narrator, **updates)
            await self._admin._log(admin_id, "update", "character_narrator", str(narrator_id), updates)
            await self._touch_catalog()
        return narrator

    async def update_scenario(
        self,
        admin_id: UUID,
        scenario_id: UUID,
        *,
        image_url: str | None = None,
        clear_image: bool = False,
    ) -> CharacterScenario:
        await self._admin.verify_admin(admin_id)
        scenario = await self._scenarios.get_by_id(scenario_id)
        if not scenario:
            raise NotFoundError("Scenario", str(scenario_id))
        updates: dict = {}
        if clear_image:
            updates["image_url"] = None
        elif image_url is not None:
            updates["image_url"] = image_url
        if updates:
            await self._scenarios.update(scenario, **updates)
            await self._admin._log(admin_id, "update", "character_scenario", str(scenario_id), updates)
            await self._touch_catalog()
        return scenario

    async def deactivate_narrator(self, admin_id: UUID, narrator_id: UUID) -> None:
        await self._admin.verify_admin(admin_id)
        narrator = await self._narrators.get_by_id(narrator_id)
        if not narrator:
            raise NotFoundError("Narrator", str(narrator_id))
        await self._narrators.deactivate(narrator)
        await self._admin._log(admin_id, "delete", "character_narrator", str(narrator_id))
        await self._touch_catalog()

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
        await self._touch_catalog()
        return character
