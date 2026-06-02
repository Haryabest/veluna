"""Admin catalog: home arts, promo codes, shop products

Revision ID: 002
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "home_art_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("image_url", sa.String(512), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "promo_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("discount_percent", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_promo_codes_code", "promo_codes", ["code"])
    op.create_table(
        "shop_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "product_type",
            sa.Enum("gems", "credits", "bundle", name="shopproducttype"),
            nullable=False,
        ),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("sale_price", sa.Integer(), nullable=True),
        sa.Column("gems_amount", sa.Integer(), server_default="0"),
        sa.Column("credits_amount", sa.Integer(), server_default="0"),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("shop_products")
    op.execute("DROP TYPE IF EXISTS shopproducttype")
    op.drop_index("ix_promo_codes_code", table_name="promo_codes")
    op.drop_table("promo_codes")
    op.drop_table("home_art_items")
