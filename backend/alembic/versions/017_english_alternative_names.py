"""Add English alternatives for catalog entities."""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "017_english_alternative_names"
down_revision: Union[str, None] = "016_user_ban_details"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("characters", sa.Column("name_en", sa.String(length=255), nullable=True))
    op.add_column("characters", sa.Column("description_en", sa.Text(), nullable=True))
    op.add_column("characters", sa.Column("subtitle_en", sa.String(length=255), nullable=True))
    op.add_column("character_scenarios", sa.Column("title_en", sa.String(length=255), nullable=True))
    op.add_column("character_scenarios", sa.Column("story_en", sa.Text(), nullable=True))
    op.add_column("character_scenarios", sa.Column("communication_style_en", sa.Text(), nullable=True))
    op.add_column("character_scenarios", sa.Column("opening_message_en", sa.Text(), nullable=True))
    op.add_column("character_narrators", sa.Column("name_en", sa.String(length=255), nullable=True))
    op.add_column("character_narrators", sa.Column("description_en", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("character_narrators", "description_en")
    op.drop_column("character_narrators", "name_en")
    op.drop_column("character_scenarios", "opening_message_en")
    op.drop_column("character_scenarios", "communication_style_en")
    op.drop_column("character_scenarios", "story_en")
    op.drop_column("character_scenarios", "title_en")
    op.drop_column("characters", "subtitle_en")
    op.drop_column("characters", "description_en")
    op.drop_column("characters", "name_en")
