"""message reply/delete + chat ai reply status

Revision ID: 013_message_actions
Revises: 012_character_narrators
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013_message_actions"
down_revision: Union[str, None] = "012_character_narrators"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_uuid = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.add_column(
        "chats",
        sa.Column("ai_reply_status", sa.String(20), server_default="idle", nullable=False),
    )
    op.add_column("chats", sa.Column("ai_reply_error", sa.Text(), nullable=True))

    op.add_column("messages", sa.Column("reply_to_id", _uuid, sa.ForeignKey("messages.id", ondelete="SET NULL"), nullable=True))
    op.add_column(
        "messages",
        sa.Column("deleted_for_all", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "messages",
        sa.Column(
            "hidden_for_users",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    op.create_index("ix_messages_reply_to_id", "messages", ["reply_to_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_reply_to_id", table_name="messages")
    op.drop_column("messages", "hidden_for_users")
    op.drop_column("messages", "deleted_for_all")
    op.drop_column("messages", "reply_to_id")
    op.drop_column("chats", "ai_reply_error")
    op.drop_column("chats", "ai_reply_status")
