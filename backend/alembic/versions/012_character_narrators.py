"""character narrators

Revision ID: 012_character_narrators
Revises: 011_generation_model_id
"""
from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_character_narrators"
down_revision: Union[str, None] = "011_generation_model_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_uuid = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "character_narrators",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column("character_id", _uuid, sa.ForeignKey("characters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("price", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_character_narrators_character_id", "character_narrators", ["character_id"])

    op.add_column(
        "chats",
        sa.Column("narrator_id", _uuid, sa.ForeignKey("character_narrators.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_chats_narrator_id", "chats", ["narrator_id"])

    op.drop_index("ix_chats_user_character_scenario_active", table_name="chats")
    op.create_index(
        "ix_chats_user_character_scenario_narrator_active",
        "chats",
        ["user_id", "character_id", "scenario_id", "narrator_id"],
        unique=True,
        postgresql_where=sa.text(
            "status = 'active' AND scenario_id IS NOT NULL AND narrator_id IS NOT NULL"
        ),
    )

    conn = op.get_bind()
    characters = conn.execute(sa.text("SELECT id FROM characters")).fetchall()
    for (character_id,) in characters:
        narrator_id = uuid.uuid4()
        conn.execute(
            sa.text(
                """
                INSERT INTO character_narrators
                    (id, character_id, name, description, price, is_active, sort_order, created_at, updated_at)
                VALUES
                    (:id, :character_id, 'Классический', 'Стандартный рассказчик', 0, true, 0, now(), now())
                """
            ),
            {"id": narrator_id, "character_id": character_id},
        )


def downgrade() -> None:
    op.drop_index("ix_chats_user_character_scenario_narrator_active", table_name="chats")
    op.create_index(
        "ix_chats_user_character_scenario_active",
        "chats",
        ["user_id", "character_id", "scenario_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active' AND scenario_id IS NOT NULL"),
    )
    op.drop_index("ix_chats_narrator_id", table_name="chats")
    op.drop_column("chats", "narrator_id")
    op.drop_index("ix_character_narrators_character_id", table_name="character_narrators")
    op.drop_table("character_narrators")
