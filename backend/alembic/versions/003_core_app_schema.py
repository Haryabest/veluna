"""Core app schema: chats, generations, payments, analytics

Revision ID: 003
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ts = sa.DateTime(timezone=True)
_uuid = postgresql.UUID(as_uuid=True)


def _ensure_enum(name: str, values: tuple[str, ...]) -> None:
    labels = ", ".join(f"'{v}'" for v in values)
    op.execute(
        f"""
        DO $$ BEGIN
            CREATE TYPE {name} AS ENUM ({labels});
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )


def upgrade() -> None:
    op.create_table(
        "user_balances",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column("user_id", _uuid, sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("gems", sa.Integer(), server_default="0"),
        sa.Column("total_spent", sa.Integer(), server_default="0"),
        sa.Column("total_earned", sa.Integer(), server_default="0"),
        sa.Column("created_at", _ts, server_default=sa.func.now()),
        sa.Column("updated_at", _ts, server_default=sa.func.now()),
    )

    op.create_table(
        "characters",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("personality_prompt", sa.Text(), server_default=""),
        sa.Column("greeting_message", sa.Text(), server_default=""),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("preview_url", sa.String(512), nullable=True),
        sa.Column("tags", postgresql.JSONB(), server_default="[]"),
        sa.Column("category", sa.String(100), server_default="general"),
        sa.Column("message_price", sa.Integer(), server_default="1"),
        sa.Column("generation_price", sa.Integer(), server_default="10"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("is_hidden", sa.Boolean(), server_default="false"),
        sa.Column("is_nsfw", sa.Boolean(), server_default="false"),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", _ts, server_default=sa.func.now()),
        sa.Column("updated_at", _ts, server_default=sa.func.now()),
    )
    op.create_index("ix_characters_slug", "characters", ["slug"])

    _ensure_enum("chatstatus", ("active", "archived"))
    op.create_table(
        "chats",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column("user_id", _uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("character_id", _uuid, sa.ForeignKey("characters.id"), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("active", "archived", name="chatstatus", create_type=False),
            server_default="active",
        ),
        sa.Column("context_summary", sa.Text(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), server_default="0"),
        sa.Column("message_count", sa.Integer(), server_default="0"),
        sa.Column("last_message_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.func.now()),
        sa.Column("updated_at", _ts, server_default=sa.func.now()),
    )
    op.create_index("ix_chats_user_id", "chats", ["user_id"])
    op.create_index("ix_chats_character_id", "chats", ["character_id"])

    _ensure_enum("messagerole", ("user", "assistant", "system"))
    op.create_table(
        "messages",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column("chat_id", _uuid, sa.ForeignKey("chats.id"), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("user", "assistant", "system", name="messagerole", create_type=False),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), server_default="0"),
        sa.Column("is_regenerated", sa.Boolean(), server_default="false"),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", _ts, server_default=sa.func.now()),
        sa.Column("updated_at", _ts, server_default=sa.func.now()),
    )
    op.create_index("ix_messages_chat_id", "messages", ["chat_id"])

    _ensure_enum(
        "generationstatus", ("pending", "processing", "completed", "failed", "moderated")
    )
    op.create_table(
        "generations",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column("user_id", _uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("character_id", _uuid, sa.ForeignKey("characters.id"), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("negative_prompt", sa.Text(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "processing",
                "completed",
                "failed",
                "moderated",
                name="generationstatus",
                create_type=False,
            ),
            server_default="pending",
        ),
        sa.Column("image_url", sa.String(512), nullable=True),
        sa.Column("thumbnail_url", sa.String(512), nullable=True),
        sa.Column("gems_cost", sa.Integer(), server_default="0"),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("task_id", sa.String(255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", _ts, server_default=sa.func.now()),
        sa.Column("updated_at", _ts, server_default=sa.func.now()),
    )
    op.create_index("ix_generations_user_id", "generations", ["user_id"])

    _ensure_enum(
        "transactiontype", ("purchase", "spend", "refund", "bonus", "admin_adjust")
    )
    op.create_table(
        "transactions",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column("user_id", _uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "purchase",
                "spend",
                "refund",
                "bonus",
                "admin_adjust",
                name="transactiontype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(512), server_default=""),
        sa.Column("reference_id", sa.String(255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", _ts, server_default=sa.func.now()),
        sa.Column("updated_at", _ts, server_default=sa.func.now()),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])

    _ensure_enum("purchasestatus", ("pending", "completed", "failed", "refunded"))
    op.create_table(
        "purchases",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column("user_id", _uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("gems_amount", sa.Integer(), nullable=False),
        sa.Column("stars_amount", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "completed",
                "failed",
                "refunded",
                name="purchasestatus",
                create_type=False,
            ),
            server_default="pending",
        ),
        sa.Column("telegram_payment_id", sa.String(255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", _ts, server_default=sa.func.now()),
        sa.Column("updated_at", _ts, server_default=sa.func.now()),
    )
    op.create_index("ix_purchases_user_id", "purchases", ["user_id"])

    _ensure_enum("subscriptionstatus", ("active", "cancelled", "expired"))
    op.create_table(
        "subscriptions",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column("user_id", _uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", sa.String(100), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active",
                "cancelled",
                "expired",
                name="subscriptionstatus",
                create_type=False,
            ),
            server_default="active",
        ),
        sa.Column("gems_per_month", sa.Integer(), server_default="0"),
        sa.Column("expires_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.func.now()),
        sa.Column("updated_at", _ts, server_default=sa.func.now()),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])

    op.create_table(
        "admin_logs",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column("admin_id", _uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("details", postgresql.JSONB(), server_default="{}"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", _ts, server_default=sa.func.now()),
        sa.Column("updated_at", _ts, server_default=sa.func.now()),
    )
    op.create_index("ix_admin_logs_admin_id", "admin_logs", ["admin_id"])

    op.create_table(
        "analytics_events",
        sa.Column("id", _uuid, primary_key=True),
        sa.Column("user_id", _uuid, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_data", postgresql.JSONB(), server_default="{}"),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("created_at", _ts, server_default=sa.func.now()),
        sa.Column("updated_at", _ts, server_default=sa.func.now()),
    )
    op.create_index("ix_analytics_events_user_id", "analytics_events", ["user_id"])
    op.create_index("ix_analytics_events_event_type", "analytics_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("analytics_events")
    op.drop_table("admin_logs")
    op.drop_table("subscriptions")
    op.execute("DROP TYPE IF EXISTS subscriptionstatus")
    op.drop_table("purchases")
    op.execute("DROP TYPE IF EXISTS purchasestatus")
    op.drop_table("transactions")
    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.drop_table("generations")
    op.execute("DROP TYPE IF EXISTS generationstatus")
    op.drop_table("messages")
    op.execute("DROP TYPE IF EXISTS messagerole")
    op.drop_table("chats")
    op.execute("DROP TYPE IF EXISTS chatstatus")
    op.drop_index("ix_characters_slug", table_name="characters")
    op.drop_table("characters")
    op.drop_table("user_balances")
