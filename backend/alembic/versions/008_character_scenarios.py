"""Character subtitle, behavior_params, scenarios table

Revision ID: 008
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_character_scenarios"
down_revision: Union[str, None] = "007_shop_product_image"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ts = sa.DateTime(timezone=True)
_uuid = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.add_column("characters", sa.Column("subtitle", sa.String(255), nullable=True))
    op.add_column(
        "characters",
        sa.Column("behavior_params", postgresql.JSONB(), server_default="[]", nullable=False),
    )

    op.create_table(
        "character_scenarios",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column("character_id", _uuid, sa.ForeignKey("characters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("story", sa.Text(), server_default="", nullable=False),
        sa.Column("communication_style", sa.Text(), server_default="", nullable=False),
        sa.Column("opening_message", sa.Text(), server_default="", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", _ts, server_default=sa.func.now()),
        sa.Column("updated_at", _ts, server_default=sa.func.now()),
    )
    op.create_index("ix_character_scenarios_character_id", "character_scenarios", ["character_id"])


def downgrade() -> None:
    op.drop_index("ix_character_scenarios_character_id", table_name="character_scenarios")
    op.drop_table("character_scenarios")
    op.drop_column("characters", "behavior_params")
    op.drop_column("characters", "subtitle")
