from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, UserBalance, UserRole


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(User).options(selectinload(User.balance)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self._session.execute(
            select(User).options(selectinload(User.balance)).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_first_active(self) -> User | None:
        result = await self._session.execute(
            select(User)
            .options(selectinload(User.balance))
            .where(User.is_active.is_(True), User.is_banned.is_(False))
            .order_by(User.created_at.asc())
            .limit(1)
        )
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
            if not hasattr(user, key):
                continue
            # Allow explicit False for is_banned / is_active
            if value is None:
                continue
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
            select(User)
            .options(selectinload(User.balance))
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    def _search_filter(self, query: str):
        raw = query.strip()
        if not raw:
            return None
        term = raw.lstrip("@").strip()
        pattern = f"%{term}%"
        clauses = [
            User.username.ilike(pattern),
            User.first_name.ilike(pattern),
            User.last_name.ilike(pattern),
        ]
        if term.isdigit():
            clauses.append(User.telegram_id == int(term))
        return or_(*clauses)

    async def search_paginated(
        self, query: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[User], int]:
        clause = self._search_filter(query)
        if clause is None:
            return [], 0
        base = select(User).options(selectinload(User.balance)).where(clause)
        total = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            base.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def is_admin(self, user: User) -> bool:
        return user.role == UserRole.ADMIN
