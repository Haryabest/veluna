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


TopUpCurrency = Literal["gems", "credits"]


class TopUpQuoteRequest(BaseSchema):
    currency_type: TopUpCurrency = "gems"
    amount: int = Field(gt=0, le=10000)
    promo_code: str | None = None


class TopUpQuoteResponse(BaseSchema):
    currency_type: TopUpCurrency
    amount: int
    promo_code: str | None = None
    discount_percent: int = 0
    promo_valid: bool = True
    promo_message: str | None = None
    stars_amount: int
    usd_amount: float
    ok: bool = True


class TopUpCheckoutRequest(BaseSchema):
    currency_type: TopUpCurrency = "gems"
    amount: int = Field(gt=0, le=10000)
    promo_code: str | None = None
    stars_amount: int = Field(gt=0)
    payment_method: PaymentMethod = "stars"
    init_data: str | None = None
