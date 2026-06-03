from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas import BaseSchema

PaymentMethod = Literal["stars"]


class PromoValidateRequest(BaseSchema):
    code: str = Field(min_length=1, max_length=64)


class PromoValidateResponse(BaseSchema):
    valid: bool
    discount_percent: int = 0
    message: str = ""


class CheckoutRequest(BaseSchema):
    product_id: UUID
    promo_code: str | None = None
    payment_method: PaymentMethod = "stars"
    # Optional: re-auth from Telegram WebApp when JWT expired (header X-Telegram-Init-Data preferred)
    init_data: str | None = None


class CheckoutResponse(BaseSchema):
    purchase_id: UUID
    invoice_url: str
    stars_amount: int
    usd_amount: float
    product_name: str
    gems_amount: int
    credits_amount: int
