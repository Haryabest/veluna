"""Insert or update test characters. Run from backend/: python -m scripts.seed_characters"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.database.session import async_session_factory
from app.models import Character
from app.seed.characters import SEED_CHARACTERS


async def seed() -> None:
    async with async_session_factory() as session:
        for data in SEED_CHARACTERS:
            existing = await session.execute(
                select(Character).where(Character.slug == data["slug"])
            )
            char = existing.scalar_one_or_none()
            if char:
                for key, value in data.items():
                    if key != "id" and hasattr(char, key):
                        setattr(char, key, value)
                print(f"Updated: {data['slug']}")
            else:
                session.add(Character(**data))
                print(f"Created: {data['slug']}")
        await session.commit()
    print(f"Done — {len(SEED_CHARACTERS)} characters ready.")


if __name__ == "__main__":
    asyncio.run(seed())
