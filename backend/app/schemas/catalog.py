from uuid import UUID

from pydantic import Field

from app.schemas import BaseSchema


class HomeArtResponse(BaseSchema):
    id: UUID
    title: str
    description: str
    image_url: str | None
    sort_order: int


class PromoCodeResponse(BaseSchema):
    id: UUID
    code: str
    name: str
    discount_percent: int
    is_active: bool
    used_count: int


class ShopProductResponse(BaseSchema):
    id: UUID
    name: str
    product_type: str
    price: int
    sale_price: int | None
    gems_amount: int
    credits_amount: int
    sort_order: int
