"""Seed test characters for development

Revision ID: 004
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.seed.characters import SEED_CHARACTERS

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

characters = sa.table(
    "characters",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("name", sa.String),
    sa.column("slug", sa.String),
    sa.column("description", sa.Text),
    sa.column("personality_prompt", sa.Text),
    sa.column("greeting_message", sa.Text),
    sa.column("avatar_url", sa.String),
    sa.column("preview_url", sa.String),
    sa.column("tags", postgresql.JSONB),
    sa.column("category", sa.String),
    sa.column("message_price", sa.Integer),
    sa.column("generation_price", sa.Integer),
    sa.column("is_active", sa.Boolean),
    sa.column("is_hidden", sa.Boolean),
    sa.column("is_nsfw", sa.Boolean),
    sa.column("sort_order", sa.Integer),
)


def upgrade() -> None:
    conn = op.get_bind()
    for char in SEED_CHARACTERS:
        exists = conn.execute(
            sa.text("SELECT 1 FROM characters WHERE slug = :slug"),
            {"slug": char["slug"]},
        ).first()
        if not exists:
            conn.execute(
                characters.insert().values(
                    id=char["id"],
                    name=char["name"],
                    slug=char["slug"],
                    description=char["description"],
                    personality_prompt=char["personality_prompt"],
                    greeting_message=char["greeting_message"],
                    avatar_url=char["avatar_url"],
                    preview_url=char["preview_url"],
                    tags=char["tags"],
                    category=char["category"],
                    message_price=char["message_price"],
                    generation_price=char["generation_price"],
                    is_active=char["is_active"],
                    is_hidden=char["is_hidden"],
                    is_nsfw=char["is_nsfw"],
                    sort_order=char["sort_order"],
                )
            )


def downgrade() -> None:
    slugs = [c["slug"] for c in SEED_CHARACTERS]
    op.execute(characters.delete().where(characters.c.slug.in_(slugs)))
