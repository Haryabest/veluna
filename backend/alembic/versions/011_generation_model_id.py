"""generation model id

Revision ID: 011_generation_model_id
Revises: 010_chat_scenario
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011_generation_model_id"
down_revision: Union[str, None] = "010_chat_scenario"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("generations", sa.Column("model_id", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("generations", "model_id")
