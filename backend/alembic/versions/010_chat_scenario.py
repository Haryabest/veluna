"""chat per scenario

Revision ID: 010_chat_scenario
Revises: 009_chat_title_pin
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_chat_scenario"
down_revision: Union[str, None] = "009_chat_title_pin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_uuid = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.add_column(
        "chats",
        sa.Column("scenario_id", _uuid, sa.ForeignKey("character_scenarios.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_chats_scenario_id", "chats", ["scenario_id"])
    op.create_index(
        "ix_chats_user_character_scenario_active",
        "chats",
        ["user_id", "character_id", "scenario_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active' AND scenario_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_chats_user_character_scenario_active", table_name="chats")
    op.drop_index("ix_chats_scenario_id", table_name="chats")
    op.drop_column("chats", "scenario_id")
