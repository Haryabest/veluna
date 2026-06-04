from __future__ import annotations

from uuid import UUID

import httpx

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models import Purchase, PurchaseStatus, ShopProduct
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.generation_repository import PaymentRepository
from app.schemas.shop import (
    CheckoutResponse,
    PromoValidateResponse,
    TopUpCheckoutRequest,
    TopUpQuoteRequest,
    TopUpQuoteResponse,
)


STARS_TO_USD = 0.02  # display estimate only


class ShopService:
    def __init__(self, session):
        self._session = session
        self._catalog = CatalogRepository(session)
        self._payments = PaymentRepository(session)

    async def validate_promo(self, code: str) -> PromoValidateResponse:
        normalized = code.strip().upper()
        if not normalized:
            return PromoValidateResponse(valid=False, message="Введите промокод")
        promo = await self._catalog.get_promo_by_code(normalized)
        if not promo or not promo.is_active:
            return PromoValidateResponse(valid=False, message="Промокод не найден")
        if promo.max_uses is not None and promo.used_count >= promo.max_uses:
            return PromoValidateResponse(valid=False, message="Промокод исчерпан")
        return PromoValidateResponse(
            valid=True,
            discount_percent=promo.discount_percent,
            message=f"Скидка {promo.discount_percent}%",
        )

    def _stars_price(self, product: ShopProduct, discount_percent: int = 0) -> int:
        base = product.sale_price if product.sale_price is not None else product.price
        if discount_percent > 0:
            base = max(1, int(base * (100 - discount_percent) / 100))
        return max(1, base)

    async def topup_quote(self, data: TopUpQuoteRequest) -> TopUpQuoteResponse:
        promo_code = (data.promo_code or "").strip().upper()
        discount = 0
        promo_valid = True
        promo_message = None
        if promo_code:
            promo_result = await self.validate_promo(promo_code)
            promo_valid = promo_result.valid
            discount = promo_result.discount_percent if promo_result.valid else 0
            promo_message = promo_result.message if promo_result.valid else promo_result.message

        unit_stars = 1 if data.currency_type == "gems" else 2
        subtotal = data.amount * unit_stars
        stars_amount = max(1, int(subtotal * (100 - discount) / 100)) if discount else max(1, subtotal)

        return TopUpQuoteResponse(
            currency_type=data.currency_type,
            amount=data.amount,
            promo_code=promo_code or None,
            discount_percent=discount,
            promo_valid=promo_valid if not promo_code else promo_valid,
            promo_message=promo_message,
            stars_amount=stars_amount,
            usd_amount=round(stars_amount * STARS_TO_USD, 2),
        )

    async def topup_checkout(self, user_id: UUID, data: TopUpCheckoutRequest) -> CheckoutResponse:
        quote = await self.topup_quote(
            TopUpQuoteRequest(
                currency_type=data.currency_type,
                amount=data.amount,
                promo_code=data.promo_code,
            )
        )
        if data.stars_amount != quote.stars_amount:
            raise ValidationError("Сумма устарела — пересчитайте пополнение")

        label = "гемов" if data.currency_type == "gems" else "сердец"
        product_name = f"Пополнение {data.amount} {label}"
        purchase = Purchase(
            user_id=user_id,
            gems_amount=data.amount if data.currency_type == "gems" else 0,
            stars_amount=quote.stars_amount,
            status=PurchaseStatus.PENDING,
            metadata_={
                "topup": True,
                "currency_type": data.currency_type,
                "credits_amount": data.amount if data.currency_type == "credits" else 0,
                "product_name": product_name,
                "promo_code": quote.promo_code,
                "discount_percent": quote.discount_percent,
            },
        )
        self._session.add(purchase)
        await self._session.flush()

        invoice_url = await self._create_invoice_link(
            title=product_name[:32],
            description=f"Veluna — {product_name}",
            payload=f"purchase:{purchase.id}",
            stars=quote.stars_amount,
        )

        return CheckoutResponse(
            purchase_id=purchase.id,
            invoice_url=invoice_url,
            stars_amount=quote.stars_amount,
            usd_amount=quote.usd_amount,
            product_name=product_name,
            gems_amount=purchase.gems_amount,
            credits_amount=int(purchase.metadata_.get("credits_amount") or 0),
        )

    async def checkout(self, user_id: UUID, product_id: UUID, promo_code: str | None = None) -> CheckoutResponse:
        await self._expire_stale_pending(user_id)
        product = await self._catalog.get_product(product_id)
        if not product or not product.is_active:
            raise NotFoundError("ShopProduct", str(product_id))

        discount = 0
        promo_normalized = None
        if promo_code:
            promo_result = await self.validate_promo(promo_code)
            if not promo_result.valid:
                raise ValidationError(promo_result.message)
            discount = promo_result.discount_percent
            promo_normalized = promo_code.strip().upper()

        stars = self._stars_price(product, discount)
        usd = round(stars * STARS_TO_USD, 2)

        purchase = Purchase(
            user_id=user_id,
            gems_amount=product.gems_amount,
            stars_amount=stars,
            status=PurchaseStatus.PENDING,
            metadata_={
                "product_id": str(product.id),
                "product_name": product.name,
                "product_type": product.product_type.value,
                "credits_amount": product.credits_amount,
                "promo_code": promo_normalized,
                "discount_percent": discount,
            },
        )
        self._session.add(purchase)
        await self._session.flush()

        payload = f"purchase:{purchase.id}"
        invoice_url = await self._create_invoice_link(
            title=product.name,
            description=f"Veluna — {product.name}",
            payload=payload,
            stars=stars,
        )

        self._track("shop_checkout_created", user_id, {"product_id": str(product.id), "stars": stars})

        return CheckoutResponse(
            purchase_id=purchase.id,
            invoice_url=invoice_url,
            stars_amount=stars,
            usd_amount=usd,
            product_name=product.name,
            gems_amount=product.gems_amount,
            credits_amount=product.credits_amount,
        )

    async def _expire_stale_pending(self, user_id: UUID) -> None:
        from datetime import datetime, timedelta, timezone

        from sqlalchemy import update

        from app.models import Purchase, PurchaseStatus

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        await self._session.execute(
            update(Purchase)
            .where(
                Purchase.user_id == user_id,
                Purchase.status == PurchaseStatus.PENDING,
                Purchase.created_at < cutoff,
            )
            .values(status=PurchaseStatus.FAILED)
        )

    async def complete_purchase(self, purchase_id: UUID, telegram_payment_id: str) -> None:
        purchase = await self._catalog.get_purchase(purchase_id)
        if not purchase:
            raise NotFoundError("Purchase", str(purchase_id))
        if purchase.status == PurchaseStatus.COMPLETED:
            return

        purchase.status = PurchaseStatus.COMPLETED
        purchase.telegram_payment_id = telegram_payment_id

        meta = purchase.metadata_ or {}
        gems = purchase.gems_amount or 0
        credits = int(meta.get("credits_amount") or 0)
        product_name = meta.get("product_name") or "Покупка"

        if gems > 0:
            from app.models import TransactionType

            await self._payments.add_gems(
                purchase.user_id,
                gems,
                TransactionType.PURCHASE,
                f"Покупка: {product_name}",
            )

        if credits > 0:
            await self._payments.add_credits(
                purchase.user_id,
                credits,
                f"Покупка: {product_name}",
            )
            purchase.metadata_ = {**meta, "credits_granted": credits}

        promo_code = meta.get("promo_code")
        if promo_code:
            promo = await self._catalog.get_promo_by_code(promo_code)
            if promo:
                promo.used_count += 1

        self._track(
            "shop_purchase_completed",
            purchase.user_id,
            {
                "purchase_id": str(purchase.id),
                "stars": purchase.stars_amount,
                "gems": gems,
                "credits": credits,
            },
        )

    def _track(self, event_type: str, user_id: UUID, event_data: dict | None = None) -> None:
        try:
            from app.tasks.analytics_tasks import track_event

            track_event.delay(str(user_id), event_type, event_data or {})
        except Exception:
            pass

    async def approve_pre_checkout(self, payload: str) -> bool:
        if not payload.startswith("purchase:"):
            return False
        try:
            purchase_id = UUID(payload.split(":", 1)[1])
        except ValueError:
            return False
        purchase = await self._catalog.get_purchase(purchase_id)
        return purchase is not None and purchase.status == PurchaseStatus.PENDING

    async def _create_invoice_link(self, title: str, description: str, payload: str, stars: int) -> str:
        settings = get_settings()
        if not settings.telegram_bot_token:
            raise ValidationError("Bot token not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/createInvoiceLink",
                json={
                    "title": title[:32],
                    "description": description[:255],
                    "payload": payload[:128],
                    "currency": "XTR",
                    "prices": [{"label": title[:32], "amount": stars}],
                },
            )
            data = response.json()
            if not data.get("ok"):
                err = data.get("description", "Не удалось создать счёт")
                if "provider" in err.lower():
                    raise ValidationError(
                        "Ошибка Telegram Payments. В @BotFather → Payments удалите "
                        "карточные провайдеры; для Stars они не нужны."
                    )
                raise ValidationError(err)
            return data["result"]
