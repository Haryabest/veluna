"""seed shop products

Revision ID: 005_seed_shop
Revises: 004
"""
from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_seed_shop"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

products = sa.table(
    "shop_products",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("name", sa.String),
    sa.column("product_type", sa.Enum("gems", "credits", "bundle", name="shopproducttype")),
    sa.column("price", sa.Integer),
    sa.column("sale_price", sa.Integer),
    sa.column("gems_amount", sa.Integer),
    sa.column("credits_amount", sa.Integer),
    sa.column("sort_order", sa.Integer),
    sa.column("is_active", sa.Boolean),
    sa.column("created_at", sa.DateTime),
    sa.column("updated_at", sa.DateTime),
)

ROWS = [
    ("Стартовый набор", "bundle", 150, 99, 200, 50, 1),
    ("Премиум набор", "bundle", 500, 399, 800, 200, 2),
    ("100 гемов", "gems", 50, None, 100, 0, 10),
    ("500 гемов", "gems", 200, 179, 500, 0, 11),
    ("1500 гемов", "gems", 500, None, 1500, 0, 12),
    ("50 кредитов", "credits", 80, None, 0, 50, 20),
    ("200 кредитов", "credits", 280, 249, 0, 200, 21),
]


def upgrade() -> None:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    op.bulk_insert(
        products,
        [
            {
                "id": uuid4(),
                "name": name,
                "product_type": ptype,
                "price": price,
                "sale_price": sale,
                "gems_amount": gems,
                "credits_amount": credits,
                "sort_order": order,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
            for name, ptype, price, sale, gems, credits, order in ROWS
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM shop_products"))
