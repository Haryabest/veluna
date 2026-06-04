from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import ChatStatus
from app.providers.ai.base import ChatMessage
from app.providers.factory import get_chat_provider
from app.repositories.character_repository import CharacterRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.generation_repository import PaymentRepository
from app.schemas import ChatListResponse, ChatResponse, MessageResponse


class ChatService:
    MAX_CONTEXT_MESSAGES = 20

    def __init__(self, session: AsyncSession):
        self._session = session
        self._chats = ChatRepository(session)
        self._characters = CharacterRepository(session)
        self._payments = PaymentRepository(session)
        self._ai = get_chat_provider()

    async def get_or_create_chat(self, user_id: UUID, character_id: UUID) -> ChatResponse:
        character = await self._characters.get_by_id(character_id)
        if not character or not character.is_active:
            raise NotFoundError("Character", str(character_id))

        chat = await self._chats.get_user_chat(user_id, character_id)
        if not chat:
            chat = await self._chats.create(user_id, character_id)
            if character.greeting_message:
                await self._chats.add_message(chat.id, "assistant", character.greeting_message)

        return ChatResponse.model_validate(chat)

    async def send_message(self, user_id: UUID, chat_id: UUID, content: str) -> MessageResponse:
        chat = await self._chats.get_by_id(chat_id)
        if not chat or chat.user_id != user_id:
            raise NotFoundError("Chat", str(chat_id))

        character = await self._characters.get_by_id(chat.character_id)
        if not character:
            raise NotFoundError("Character", str(chat.character_id))

        await self._payments.deduct_gems(
            user_id,
            character.message_price,
            f"Message to {character.name}",
            reference_id=str(chat_id),
        )

        user_msg = await self._chats.add_message(chat_id, "user", content)

        history = await self._chats.get_messages(chat_id, limit=self.MAX_CONTEXT_MESSAGES)
        ai_messages = [ChatMessage(role=m.role.value, content=m.content) for m in history]

        from app.providers.ai.base import ChatCompletionRequest

        response = await self._ai.complete(
            ChatCompletionRequest(
                messages=ai_messages,
                system_prompt=character.personality_prompt,
            )
        )

        assistant_msg = await self._chats.add_message(
            chat_id, "assistant", response.content, tokens_used=response.tokens_used
        )

        from app.tasks.chat_tasks import process_chat_analytics
        process_chat_analytics.delay(str(user_id), str(chat_id), response.tokens_used)

        return MessageResponse.model_validate(assistant_msg)

    async def get_messages(self, user_id: UUID, chat_id: UUID, limit: int = 50) -> list[MessageResponse]:
        chat = await self._chats.get_by_id(chat_id)
        if not chat or chat.user_id != user_id:
            raise NotFoundError("Chat", str(chat_id))

        messages = await self._chats.get_messages(chat_id, limit=limit)
        return [MessageResponse.model_validate(m) for m in messages]

    async def list_user_chats(self, user_id: UUID, page: int = 1) -> tuple[list[ChatListResponse], int]:
        chats, total = await self._chats.list_user_chats(user_id, page=page)
        items: list[ChatListResponse] = []
        for chat in chats:
            character = chat.character
            if not character:
                character = await self._characters.get_by_id(chat.character_id)
            preview = await self._chats.get_last_message_preview(chat.id)
            name = character.name if character else "Персонаж"
            items.append(
                ChatListResponse(
                    id=chat.id,
                    character_id=chat.character_id,
                    character_name=name,
                    character_avatar_url=character.avatar_url if character else None,
                    display_title=(chat.custom_title or name).strip(),
                    is_pinned=chat.is_pinned,
                    last_message_preview=preview,
                    last_message_at=chat.last_message_at,
                    message_count=chat.message_count,
                )
            )
        return items, total

    async def update_title(self, user_id: UUID, chat_id: UUID, title: str) -> ChatListResponse:
        chat = await self._require_user_chat(user_id, chat_id)
        await self._chats.update_title(chat, title)
        return await self._to_list_item(chat)

    async def set_pinned(self, user_id: UUID, chat_id: UUID, pinned: bool) -> ChatListResponse:
        chat = await self._require_user_chat(user_id, chat_id)
        await self._chats.set_pinned(chat, pinned)
        return await self._to_list_item(chat)

    async def archive_chat(self, user_id: UUID, chat_id: UUID) -> None:
        chat = await self._require_user_chat(user_id, chat_id)
        await self._chats.archive(chat)

    async def _require_user_chat(self, user_id: UUID, chat_id: UUID):
        chat = await self._chats.get_by_id(chat_id)
        if not chat or chat.user_id != user_id or chat.status != ChatStatus.ACTIVE:
            raise NotFoundError("Chat", str(chat_id))
        return chat

    async def _to_list_item(self, chat) -> ChatListResponse:
        character = await self._characters.get_by_id(chat.character_id)
        preview = await self._chats.get_last_message_preview(chat.id)
        name = character.name if character else "Персонаж"
        return ChatListResponse(
            id=chat.id,
            character_id=chat.character_id,
            character_name=name,
            character_avatar_url=character.avatar_url if character else None,
            display_title=(chat.custom_title or name).strip(),
            is_pinned=chat.is_pinned,
            last_message_preview=preview,
            last_message_at=chat.last_message_at,
            message_count=chat.message_count,
        )
