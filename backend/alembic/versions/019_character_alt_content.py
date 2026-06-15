"""Add alt description, subtitle, behavior params for characters."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "019_character_alt_content"
down_revision = "018_localized_alt_names"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("characters", sa.Column("description_alt", sa.Text(), nullable=True))
    op.add_column("characters", sa.Column("subtitle_alt", sa.String(255), nullable=True))
    op.add_column(
        "characters",
        sa.Column("behavior_params_alt", postgresql.JSONB(), server_default="[]", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("characters", "behavior_params_alt")
    op.drop_column("characters", "subtitle_alt")
    op.drop_column("characters", "description_alt")
