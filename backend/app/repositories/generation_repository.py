from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Generation,
    GenerationStatus,
    Message,
    MessageRole,
    Purchase,
    PurchaseStatus,
    Transaction,
    TransactionType,
    UserBalance,
)


def _transaction_currency(tx: Transaction) -> str:
    meta = tx.metadata_ or {}
    currency = meta.get("currency")
    if currency in ("gems", "credits"):
        return currency
    if meta.get("credits_after") is not None:
        return "credits"
    desc = (tx.description or "").lower()
    if any(k in desc for k in ("сообщение", "narrator", "рассказчик")):
        return "credits"
    if "image generation" in desc or "генерац" in desc:
        return "gems"
    return "gems"


class GenerationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, generation_id: UUID) -> Generation | None:
        result = await self._session.execute(select(Generation).where(Generation.id == generation_id))
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Generation:
        generation = Generation(**kwargs)
        self._session.add(generation)
        await self._session.flush()
        return generation

    async def update_status(
        self,
        generation: Generation,
        status: GenerationStatus,
        **kwargs,
    ) -> Generation:
        generation.status = status
        for key, value in kwargs.items():
            if value is not None:
                setattr(generation, key, value)
        await self._session.flush()
        return generation

    async def list_user_generations(self, user_id: UUID, page: int = 1, page_size: int = 20) -> tuple[list[Generation], int]:
        query = select(Generation).where(Generation.user_id == user_id)
        total = (await self._session.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            query.order_by(Generation.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_balance(self, user_id: UUID) -> UserBalance | None:
        result = await self._session.execute(select(UserBalance).where(UserBalance.user_id == user_id))
        return result.scalar_one_or_none()

    async def deduct_gems(
        self,
        user_id: UUID,
        amount: int,
        description: str,
        reference_id: str | None = None,
        *,
        extra_metadata: dict | None = None,
    ) -> UserBalance:
        balance = await self.get_balance(user_id)
        if not balance or balance.gems < amount:
            from app.core.exceptions import InsufficientBalanceError
            raise InsufficientBalanceError(required=amount, available=balance.gems if balance else 0)

        balance.gems -= amount
        balance.total_spent += amount

        tx_meta = {"currency": "gems", "gems_after": balance.gems}
        if extra_metadata:
            tx_meta.update(extra_metadata)
        transaction = Transaction(
            user_id=user_id,
            type=TransactionType.SPEND,
            amount=-amount,
            balance_after=balance.gems,
            description=description,
            reference_id=reference_id,
            metadata_=tx_meta,
        )
        self._session.add(transaction)
        await self._session.flush()
        return balance

    async def add_gems(self, user_id: UUID, amount: int, tx_type: TransactionType, description: str) -> UserBalance:
        balance = await self.get_balance(user_id)
        if not balance:
            balance = UserBalance(user_id=user_id, gems=0, credits=0)
            self._session.add(balance)
            await self._session.flush()

        balance.gems += amount
        balance.total_earned += amount

        transaction = Transaction(
            user_id=user_id,
            type=tx_type,
            amount=amount,
            balance_after=balance.gems,
            description=description,
            metadata_={"currency": "gems", "gems_after": balance.gems},
        )
        self._session.add(transaction)
        await self._session.flush()
        return balance

    async def add_credits(
        self,
        user_id: UUID,
        amount: int,
        description: str,
        *,
        tx_type: TransactionType = TransactionType.PURCHASE,
    ) -> UserBalance:
        balance = await self.get_balance(user_id)
        if not balance:
            balance = UserBalance(user_id=user_id, gems=0, credits=0)
            self._session.add(balance)
            await self._session.flush()

        balance.credits += amount
        balance.total_earned += amount

        transaction = Transaction(
            user_id=user_id,
            type=tx_type,
            amount=amount,
            balance_after=balance.credits,
            description=description,
            metadata_={"currency": "credits", "credits_after": balance.credits},
        )
        self._session.add(transaction)
        await self._session.flush()
        return balance

    async def deduct_credits(
        self,
        user_id: UUID,
        amount: int,
        description: str,
        reference_id: str | None = None,
        *,
        extra_metadata: dict | None = None,
    ) -> UserBalance:
        balance = await self.get_balance(user_id)
        if not balance or balance.credits < amount:
            from app.core.exceptions import InsufficientBalanceError

            raise InsufficientBalanceError(
                required=amount,
                available=balance.credits if balance else 0,
                currency="credits",
            )

        balance.credits -= amount
        balance.total_spent += amount

        tx_meta = {"currency": "credits", "credits_after": balance.credits}
        if extra_metadata:
            tx_meta.update(extra_metadata)
        transaction = Transaction(
            user_id=user_id,
            type=TransactionType.SPEND,
            amount=-amount,
            balance_after=balance.gems,
            description=description,
            reference_id=reference_id,
            metadata_=tx_meta,
        )
        self._session.add(transaction)
        await self._session.flush()
        return balance

    async def set_balance(
        self,
        user_id: UUID,
        *,
        gems: int | None = None,
        credits: int | None = None,
    ) -> UserBalance:
        balance = await self.get_balance(user_id)
        if not balance:
            balance = UserBalance(user_id=user_id, gems=0, credits=0)
            self._session.add(balance)
            await self._session.flush()
        if gems is not None:
            balance.gems = gems
        if credits is not None:
            balance.credits = credits
        await self._session.flush()
        return balance

    async def list_transactions(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        kind: str | None = None,
    ) -> tuple[list[Transaction], int]:
        query = select(Transaction).where(Transaction.user_id == user_id)
        if kind == "expense":
            query = query.where(Transaction.amount < 0)
        elif kind == "deposit":
            query = query.where(Transaction.amount > 0)
        total = (await self._session.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            query.order_by(Transaction.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_spending_summary(self, user_id: UUID) -> dict[str, int]:
        stats = await self.get_finance_stats(user_id)
        return {
            "gems_spent": stats["spent"]["gems"],
            "credits_spent": stats["spent"]["credits"],
        }

    async def get_finance_stats(self, user_id: UUID) -> dict:
        """Balance, spent, deposited totals and purchase summary."""
        balance = await self.get_balance(user_id)

        tx_result = await self._session.execute(
            select(Transaction).where(Transaction.user_id == user_id)
        )
        gems_spent = credits_spent = 0
        gems_deposited = credits_deposited = 0
        for tx in tx_result.scalars().all():
            amount = abs(int(tx.amount))
            currency = _transaction_currency(tx)
            if int(tx.amount) < 0:
                if currency == "credits":
                    credits_spent += amount
                else:
                    gems_spent += amount
            elif int(tx.amount) > 0:
                if currency == "credits":
                    credits_deposited += amount
                else:
                    gems_deposited += amount

        purchase_result = await self._session.execute(
            select(Purchase).where(
                Purchase.user_id == user_id,
                Purchase.status == PurchaseStatus.COMPLETED,
            )
        )
        purchases = list(purchase_result.scalars().all())
        stars_total = 0
        gems_from_purchases = 0
        credits_from_purchases = 0
        for purchase in purchases:
            stars_total += int(purchase.stars_amount or 0)
            gems_from_purchases += int(purchase.gems_amount or 0)
            meta = purchase.metadata_ or {}
            credits_from_purchases += int(meta.get("credits_granted") or meta.get("credits_amount") or 0)

        return {
            "balance": {
                "gems": int(balance.gems if balance else 0),
                "credits": int(balance.credits if balance else 0),
            },
            "spent": {
                "gems": gems_spent,
                "credits": credits_spent,
            },
            "deposited": {
                "gems": gems_deposited,
                "credits": credits_deposited,
            },
            "purchases": {
                "completed_count": len(purchases),
                "stars_total": stars_total,
                "gems_total": gems_from_purchases,
                "credits_total": credits_from_purchases,
            },
            "lifetime": {
                "total_earned": int(balance.total_earned if balance else 0),
                "total_spent": int(balance.total_spent if balance else 0),
            },
        }

    async def get_platform_finance_stats(self) -> dict:
        """Platform-wide totals: balances, spent, deposited, purchases."""
        tx_result = await self._session.execute(select(Transaction))
        gems_spent = credits_spent = 0
        gems_deposited = credits_deposited = 0
        for tx in tx_result.scalars().all():
            amount = abs(int(tx.amount))
            currency = _transaction_currency(tx)
            if int(tx.amount) < 0:
                if currency == "credits":
                    credits_spent += amount
                else:
                    gems_spent += amount
            elif int(tx.amount) > 0:
                if currency == "credits":
                    credits_deposited += amount
                else:
                    gems_deposited += amount

        balance_row = (
            await self._session.execute(
                select(
                    func.coalesce(func.sum(UserBalance.gems), 0),
                    func.coalesce(func.sum(UserBalance.credits), 0),
                )
            )
        ).one()

        purchase_row = (
            await self._session.execute(
                select(
                    func.count(Purchase.id),
                    func.coalesce(func.sum(Purchase.stars_amount), 0),
                    func.coalesce(func.sum(Purchase.gems_amount), 0),
                ).where(Purchase.status == PurchaseStatus.COMPLETED)
            )
        ).one()

        return {
            "balance": {
                "gems": int(balance_row[0] or 0),
                "credits": int(balance_row[1] or 0),
            },
            "spent": {"gems": gems_spent, "credits": credits_spent},
            "deposited": {"gems": gems_deposited, "credits": credits_deposited},
            "purchases": {
                "completed_count": int(purchase_row[0] or 0),
                "stars_total": int(purchase_row[1] or 0),
                "gems_total": int(purchase_row[2] or 0),
            },
        }

    async def get_platform_api_cost_stats(self) -> dict:
        """Provider costs: GenAPI rubles (chat), Civitai Buzz (images)."""
        from app.services.api_cost_service import calc_message_cost_rub, extract_civitai_buzz_cost

        msg_rows = (
            await self._session.execute(
                select(Message.tokens_used, Message.metadata_).where(
                    Message.role == MessageRole.ASSISTANT,
                    Message.tokens_used > 0,
                )
            )
        ).all()

        chat_rub = 0.0
        chat_tokens = 0
        for tokens_used, meta in msg_rows:
            chat_tokens += int(tokens_used or 0)
            chat_rub += calc_message_cost_rub(int(tokens_used or 0), meta)

        gen_rows = (
            await self._session.execute(
                select(Generation.metadata_).where(Generation.status == GenerationStatus.COMPLETED)
            )
        ).all()

        image_buzz = 0
        image_generations = 0
        for (meta,) in gen_rows:
            buzz = extract_civitai_buzz_cost(meta)
            if buzz > 0:
                image_buzz += buzz
                image_generations += 1

        return {
            "chat": {"rub": round(chat_rub, 2), "tokens": chat_tokens},
            "image": {"buzz": image_buzz, "generations": image_generations},
        }
