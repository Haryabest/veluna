"""Add name_alt / title_alt / message_text_alt for bilingual catalog."""

from alembic import op
import sqlalchemy as sa

revision = "018_localized_alt_names"
down_revision = "017_user_locale_selected"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("characters", sa.Column("name_alt", sa.String(255), nullable=True))
    op.add_column("character_scenarios", sa.Column("title_alt", sa.String(255), nullable=True))
    op.add_column("character_narrators", sa.Column("name_alt", sa.String(255), nullable=True))
    op.add_column("shop_products", sa.Column("name_alt", sa.String(255), nullable=True))
    op.add_column("broadcasts", sa.Column("message_text_alt", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("broadcasts", "message_text_alt")
    op.drop_column("shop_products", "name_alt")
    op.drop_column("character_narrators", "name_alt")
    op.drop_column("character_scenarios", "title_alt")
    op.drop_column("characters", "name_alt")
