"""Add image_url to character narrators and scenarios."""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_narrator_scenario_images"
down_revision: Union[str, None] = "013_message_actions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "character_narrators",
        sa.Column("image_url", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "character_scenarios",
        sa.Column("image_url", sa.String(length=512), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("character_scenarios", "image_url")
    op.drop_column("character_narrators", "image_url")
