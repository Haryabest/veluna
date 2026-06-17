"""Add alt story/communication for scenarios and alt description for narrators."""

from alembic import op
import sqlalchemy as sa

revision = "020_scenario_narr_alt"
down_revision = "019_character_alt_content"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("character_scenarios", sa.Column("story_alt", sa.Text(), nullable=True))
    op.add_column(
        "character_scenarios",
        sa.Column("communication_style_alt", sa.Text(), nullable=True),
    )
    op.add_column("character_narrators", sa.Column("description_alt", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("character_narrators", "description_alt")
    op.drop_column("character_scenarios", "communication_style_alt")
    op.drop_column("character_scenarios", "story_alt")
