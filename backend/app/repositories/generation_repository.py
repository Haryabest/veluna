from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Generation, GenerationStatus, Transaction, TransactionType, UserBalance


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

    async def deduct_gems(self, user_id: UUID, amount: int, description: str, reference_id: str | None = None) -> UserBalance:
        balance = await self.get_balance(user_id)
        if not balance or balance.gems < amount:
            from app.core.exceptions import InsufficientBalanceError
            raise InsufficientBalanceError(required=amount, available=balance.gems if balance else 0)

        balance.gems -= amount
        balance.total_spent += amount

        transaction = Transaction(
            user_id=user_id,
            type=TransactionType.SPEND,
            amount=-amount,
            balance_after=balance.gems,
            description=description,
            reference_id=reference_id,
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
        )
        self._session.add(transaction)
        await self._session.flush()
        return balance

    async def add_credits(self, user_id: UUID, amount: int, description: str) -> UserBalance:
        balance = await self.get_balance(user_id)
        if not balance:
            balance = UserBalance(user_id=user_id, gems=0, credits=0)
            self._session.add(balance)
            await self._session.flush()

        balance.credits += amount
        balance.total_earned += amount
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
