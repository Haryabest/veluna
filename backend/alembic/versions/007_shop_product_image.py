"""Add image_url to shop products."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_shop_product_image"
down_revision: Union[str, None] = "006_credits_broadcasts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("shop_products", sa.Column("image_url", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("shop_products", "image_url")
