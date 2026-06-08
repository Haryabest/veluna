"""Add performance indexes for chat and message queries."""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "015_chat_performance_indexes"
down_revision: Union[str, None] = "014_narrator_scenario_images"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_messages_chat_id_created_at",
        "messages",
        ["chat_id", "created_at"],
        unique=False,
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "ix_chats_user_status_last_message",
        "chats",
        ["user_id", "status", "last_message_at"],
        unique=False,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("ix_chats_user_status_last_message", table_name="chats")
    op.drop_index("ix_messages_chat_id_created_at", table_name="messages")
