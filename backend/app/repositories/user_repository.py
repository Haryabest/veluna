from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserBalance, UserRole


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self._session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def create(self, telegram_id: int, **kwargs) -> User:
        user = User(telegram_id=telegram_id, **kwargs)
        self._session.add(user)
        await self._session.flush()
        balance = UserBalance(user_id=user.id, gems=0)
        self._session.add(balance)
        await self._session.flush()
        return user

    async def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        await self._session.flush()
        return user

    async def count_all(self) -> int:
        result = await self._session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def list_paginated(self, page: int = 1, page_size: int = 20) -> tuple[list[User], int]:
        offset = (page - 1) * page_size
        total = await self.count_all()
        result = await self._session.execute(
            select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def is_admin(self, user: User) -> bool:
        return user.role == UserRole.ADMIN
