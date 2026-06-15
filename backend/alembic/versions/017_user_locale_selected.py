"""Add locale_selected flag for explicit language choice."""

from alembic import op
import sqlalchemy as sa

revision = "017_user_locale_selected"
down_revision = "016_user_ban_details"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("locale_selected", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.execute("UPDATE users SET locale_selected = true")
    op.execute(
        """
        UPDATE users
        SET language_code = CASE
            WHEN lower(language_code) LIKE 'ru%' OR language_code IN ('be', 'uk', 'kk') THEN 'ru'
            ELSE 'en'
        END
        """
    )


def downgrade() -> None:
    op.drop_column("users", "locale_selected")
