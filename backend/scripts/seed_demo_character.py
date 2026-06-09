"""Insert or update one fully configured demo character. Run: python -m scripts.seed_demo_character"""

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.database.session import async_session_factory
from app.models import Character, CharacterNarrator, CharacterScenario
from app.seed.demo_character import (
    DEMO_CHARACTER,
    DEMO_CHARACTER_SLUG,
    DEMO_NARRATORS,
    DEMO_SCENARIOS,
)
from app.repositories.character_repository import CharacterRepository
from app.services.catalog_version_service import bump_catalog_version


async def seed() -> None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(Character).where(Character.slug == DEMO_CHARACTER_SLUG)
        )
        character = result.scalar_one_or_none()

        char_data = {**DEMO_CHARACTER}
        metadata = char_data.pop("metadata", {})
        char_id = uuid.UUID(char_data.pop("id"))

        if character:
            for key, value in char_data.items():
                if hasattr(character, key):
                    setattr(character, key, value)
            character.metadata_ = metadata
            print(f"Updated character: {DEMO_CHARACTER_SLUG}")
        else:
            character = Character(id=char_id, metadata_=metadata, **char_data)
            session.add(character)
            await session.flush()
            print(f"Created character: {DEMO_CHARACTER_SLUG}")

        char_uuid = character.id

        for scen_data in DEMO_SCENARIOS:
            scen_id = uuid.UUID(scen_data["id"])
            existing = await session.get(CharacterScenario, scen_id)
            payload = {k: v for k, v in scen_data.items() if k != "id"}
            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
                existing.character_id = char_uuid
                existing.is_active = True
            else:
                session.add(
                    CharacterScenario(
                        id=scen_id,
                        character_id=char_uuid,
                        is_active=True,
                        **payload,
                    )
                )

        for narr_data in DEMO_NARRATORS:
            narr_id = uuid.UUID(narr_data["id"])
            existing = await session.get(CharacterNarrator, narr_id)
            payload = {k: v for k, v in narr_data.items() if k != "id"}
            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
                existing.character_id = char_uuid
                existing.is_active = True
            else:
                session.add(
                    CharacterNarrator(
                        id=narr_id,
                        character_id=char_uuid,
                        is_active=True,
                        **payload,
                    )
                )

        await session.commit()

        async with async_session_factory() as session:
            repo = CharacterRepository(session)
            character = await repo.get_by_id(char_uuid)
            if character:
                await repo.prepend_to_catalog(char_uuid)
                await session.commit()

    await bump_catalog_version()
    print(
        f"Done — {DEMO_CHARACTER['name']}: "
        f"{len(DEMO_SCENARIOS)} scenarios, {len(DEMO_NARRATORS)} narrators."
    )


if __name__ == "__main__":
    asyncio.run(seed())
