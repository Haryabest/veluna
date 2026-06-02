from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.providers.ai.base import ChatMessage
from app.providers.factory import get_chat_provider
from app.repositories.character_repository import CharacterRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.generation_repository import PaymentRepository
from app.schemas import ChatResponse, MessageResponse


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

    async def list_user_chats(self, user_id: UUID, page: int = 1) -> tuple[list[ChatResponse], int]:
        chats, total = await self._chats.list_user_chats(user_id, page=page)
        return [ChatResponse.model_validate(c) for c in chats], total
