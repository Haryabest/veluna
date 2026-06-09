from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AiReplyStatus, Chat, ChatStatus, Message, MessageRole
from app.utils.message_preview import format_message_preview


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def _chat_options(self, *, include_messages: bool = False):
        opts = [
            selectinload(Chat.character),
            selectinload(Chat.scenario),
            selectinload(Chat.narrator),
        ]
        if include_messages:
            opts.append(selectinload(Chat.messages))
        return opts

    async def get_by_id(self, chat_id: UUID, *, include_messages: bool = False) -> Chat | None:
        result = await self._session.execute(
            select(Chat)
            .options(*self._chat_options(include_messages=include_messages))
            .where(Chat.id == chat_id)
        )
        return result.scalar_one_or_none()

    async def get_user_chat(
        self,
        user_id: UUID,
        character_id: UUID,
        scenario_id: UUID,
        narrator_id: UUID,
    ) -> Chat | None:
        result = await self._session.execute(
            select(Chat)
            .options(selectinload(Chat.character), selectinload(Chat.scenario), selectinload(Chat.narrator))
            .where(
                Chat.user_id == user_id,
                Chat.character_id == character_id,
                Chat.scenario_id == scenario_id,
                Chat.narrator_id == narrator_id,
                Chat.status == ChatStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    async def list_user_chats(self, user_id: UUID, page: int = 1, page_size: int = 20) -> tuple[list[Chat], int]:
        filters = (Chat.user_id == user_id, Chat.status == ChatStatus.ACTIVE)
        total = (
            await self._session.execute(select(func.count()).select_from(Chat).where(*filters))
        ).scalar_one()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(Chat)
            .options(selectinload(Chat.character), selectinload(Chat.scenario), selectinload(Chat.narrator))
            .where(*filters)
            .order_by(Chat.is_pinned.desc(), Chat.last_message_at.desc().nullslast())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    def _visible_messages_filter(self, user_id: UUID):
        user_key = str(user_id)
        return (
            Message.deleted_for_all.is_(False),
            or_(
                Message.hidden_for_users.is_(None),
                ~Message.hidden_for_users.contains([user_key]),
            ),
        )

    async def get_last_message_preview(self, chat_id: UUID, user_id: UUID | None = None) -> str | None:
        previews = await self.batch_last_message_previews([chat_id], user_id)
        return previews.get(chat_id)

    async def batch_last_message_previews(
        self, chat_ids: list[UUID], user_id: UUID | None = None
    ) -> dict[UUID, str | None]:
        if not chat_ids:
            return {}

        query = select(Message.chat_id, Message.content).where(
            Message.chat_id.in_(chat_ids),
            Message.deleted_for_all.is_(False),
        )
        if user_id is not None:
            user_key = str(user_id)
            query = query.where(
                or_(
                    Message.hidden_for_users.is_(None),
                    ~Message.hidden_for_users.contains([user_key]),
                )
            )

        result = await self._session.execute(
            query.distinct(Message.chat_id).order_by(Message.chat_id, Message.created_at.desc())
        )
        previews: dict[UUID, str | None] = {cid: None for cid in chat_ids}
        for chat_id, content in result.all():
            previews[chat_id] = format_message_preview(content)
        return previews

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

    async def set_ai_reply_status(
        self,
        chat: Chat,
        status: AiReplyStatus | str,
        error: str | None = None,
    ) -> Chat:
        chat.ai_reply_status = status.value if isinstance(status, AiReplyStatus) else status
        chat.ai_reply_error = error
        await self._session.flush()
        return chat

    async def create(
        self, user_id: UUID, character_id: UUID, scenario_id: UUID, narrator_id: UUID
    ) -> Chat:
        chat = Chat(
            user_id=user_id,
            character_id=character_id,
            scenario_id=scenario_id,
            narrator_id=narrator_id,
        )
        self._session.add(chat)
        await self._session.flush()
        return chat

    async def _touch_chat_on_message(self, chat_id: UUID, tokens_used: int = 0) -> None:
        await self._session.execute(
            update(Chat)
            .where(Chat.id == chat_id)
            .values(
                message_count=Chat.message_count + 1,
                total_tokens=Chat.total_tokens + tokens_used,
                last_message_at=func.now(),
            )
        )

    async def add_message(
        self,
        chat_id: UUID,
        role: MessageRole | str,
        content: str,
        tokens_used: int = 0,
        reply_to_id: UUID | None = None,
        metadata_: dict | None = None,
    ) -> Message:
        role_enum = MessageRole(role) if isinstance(role, str) else role
        message = Message(
            chat_id=chat_id,
            role=role_enum,
            content=content,
            tokens_used=tokens_used,
            reply_to_id=reply_to_id,
            metadata_=metadata_ or {},
        )
        self._session.add(message)
        await self._touch_chat_on_message(chat_id, tokens_used)
        await self._session.flush()
        return message

    async def get_latest_message(self, chat_id: UUID) -> Message | None:
        result = await self._session.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .options(selectinload(Message.reply_to))
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_message(self, message_id: UUID, chat_id: UUID | None = None) -> Message | None:
        query = (
            select(Message)
            .where(Message.id == message_id)
            .options(selectinload(Message.reply_to))
        )
        if chat_id:
            query = query.where(Message.chat_id == chat_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_messages(
        self,
        chat_id: UUID,
        user_id: UUID,
        limit: int = 50,
        before_id: UUID | None = None,
    ) -> list[Message]:
        query = select(Message).where(Message.chat_id == chat_id, *self._visible_messages_filter(user_id))
        if before_id:
            query = query.where(Message.id < before_id)
        result = await self._session.execute(
            query.options(selectinload(Message.reply_to)).order_by(Message.created_at.desc()).limit(limit)
        )
        return list(reversed(result.scalars().all()))

    async def hide_message_for_user(self, message: Message, user_id: UUID) -> Message:
        hidden = list(message.hidden_for_users or [])
        key = str(user_id)
        if key not in hidden:
            hidden.append(key)
            message.hidden_for_users = hidden
            await self._session.flush()
        return message

    async def delete_message_for_all(self, message: Message) -> Message:
        message.deleted_for_all = True
        await self._session.execute(
            update(Chat)
            .where(Chat.id == message.chat_id, Chat.message_count > 0)
            .values(message_count=Chat.message_count - 1)
        )
        await self._session.flush()
        return message
