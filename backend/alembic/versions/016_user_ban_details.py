"""Add ban reason and expiry to users."""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "016_user_ban_details"
down_revision: Union[str, None] = "015_chat_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("ban_reason", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("banned_until", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "banned_until")
    op.drop_column("users", "ban_reason")
