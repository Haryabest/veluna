from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Chat, ChatStatus, Message, MessageRole


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, chat_id: UUID) -> Chat | None:
        result = await self._session.execute(
            select(Chat)
            .options(
                selectinload(Chat.messages),
                selectinload(Chat.character),
                selectinload(Chat.scenario),
            )
            .where(Chat.id == chat_id)
        )
        return result.scalar_one_or_none()

    async def get_user_chat(
        self, user_id: UUID, character_id: UUID, scenario_id: UUID
    ) -> Chat | None:
        result = await self._session.execute(
            select(Chat)
            .options(selectinload(Chat.character), selectinload(Chat.scenario))
            .where(
                Chat.user_id == user_id,
                Chat.character_id == character_id,
                Chat.scenario_id == scenario_id,
                Chat.status == ChatStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    async def list_user_chats(self, user_id: UUID, page: int = 1, page_size: int = 20) -> tuple[list[Chat], int]:
        query = (
            select(Chat)
            .options(selectinload(Chat.character), selectinload(Chat.scenario))
            .where(Chat.user_id == user_id, Chat.status == ChatStatus.ACTIVE)
        )
        total = (await self._session.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            query.order_by(Chat.is_pinned.desc(), Chat.last_message_at.desc().nullslast())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_last_message_preview(self, chat_id: UUID) -> str | None:
        result = await self._session.execute(
            select(Message.content)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        text = row.strip()
        return text[:120] if len(text) > 120 else text

    async def update_title(self, chat: Chat, title: str) -> Chat:
        chat.custom_title = title.strip()
        await self._session.flush()
        return chat

    async def set_pinned(self, chat: Chat, pinned: bool) -> Chat:
        chat.is_pinned = pinned
        await self._session.flush()
        return chat

    async def archive(self, chat: Chat) -> Chat:
        chat.status = ChatStatus.ARCHIVED
        chat.is_pinned = False
        await self._session.flush()
        return chat

    async def create(self, user_id: UUID, character_id: UUID, scenario_id: UUID) -> Chat:
        chat = Chat(user_id=user_id, character_id=character_id, scenario_id=scenario_id)
        self._session.add(chat)
        await self._session.flush()
        return chat

    async def add_message(self, chat_id: UUID, role: MessageRole | str, content: str, tokens_used: int = 0) -> Message:
        role_enum = MessageRole(role) if isinstance(role, str) else role
        message = Message(chat_id=chat_id, role=role_enum, content=content, tokens_used=tokens_used)
        self._session.add(message)

        chat = await self.get_by_id(chat_id)
        if chat:
            chat.message_count += 1
            chat.total_tokens += tokens_used
            chat.last_message_at = func.now()

        await self._session.flush()
        return message

    async def get_messages(self, chat_id: UUID, limit: int = 50, before_id: UUID | None = None) -> list[Message]:
        query = select(Message).where(Message.chat_id == chat_id)
        if before_id:
            query = query.where(Message.id < before_id)
        result = await self._session.execute(query.order_by(Message.created_at.desc()).limit(limit))
        return list(reversed(result.scalars().all()))
