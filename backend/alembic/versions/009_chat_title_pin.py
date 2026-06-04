"""chat custom title and pin

Revision ID: 009
Revises: 008
Create Date: 2026-06-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_chat_title_pin"
down_revision: Union[str, None] = "008_character_scenarios"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chats", sa.Column("custom_title", sa.String(255), nullable=True))
    op.add_column(
        "chats",
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("chats", "is_pinned")
    op.drop_column("chats", "custom_title")
