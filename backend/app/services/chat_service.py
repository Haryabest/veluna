from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import CharacterScenario, Chat, ChatStatus
from app.providers.ai.base import ChatMessage
from app.providers.factory import get_chat_provider
from app.repositories.character_repository import CharacterRepository
from app.repositories.character_scenario_repository import CharacterScenarioRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.generation_repository import PaymentRepository
from app.schemas import ChatListResponse, ChatResponse, MessageResponse


class ChatService:
    MAX_CONTEXT_MESSAGES = 20

    def __init__(self, session: AsyncSession):
        self._session = session
        self._chats = ChatRepository(session)
        self._characters = CharacterRepository(session)
        self._scenarios = CharacterScenarioRepository(session)
        self._payments = PaymentRepository(session)
        self._ai = get_chat_provider()

    async def get_or_create_chat(
        self, user_id: UUID, character_id: UUID, scenario_id: UUID
    ) -> ChatResponse:
        character = await self._characters.get_by_id(character_id)
        if not character or not character.is_active:
            raise NotFoundError("Character", str(character_id))

        scenario = await self._scenarios.get_by_id(scenario_id)
        if not scenario or scenario.character_id != character_id or not scenario.is_active:
            raise NotFoundError("Scenario", str(scenario_id))

        chat = await self._chats.get_user_chat(user_id, character_id, scenario_id)
        if not chat:
            chat = await self._chats.create(user_id, character_id, scenario_id)
            opening = (scenario.opening_message or "").strip() or (character.greeting_message or "").strip()
            if opening:
                await self._chats.add_message(chat.id, "assistant", opening)
            chat = await self._chats.get_by_id(chat.id)

        return self._to_chat_response(chat, character, scenario)

    async def get_chat(self, user_id: UUID, chat_id: UUID) -> ChatResponse:
        chat = await self._require_user_chat(user_id, chat_id)
        character = chat.character or await self._characters.get_by_id(chat.character_id)
        scenario = chat.scenario
        if chat.scenario_id and not scenario:
            scenario = await self._scenarios.get_by_id(chat.scenario_id)
        return self._to_chat_response(chat, character, scenario)

    async def send_message(self, user_id: UUID, chat_id: UUID, content: str) -> MessageResponse:
        chat = await self._chats.get_by_id(chat_id)
        if not chat or chat.user_id != user_id:
            raise NotFoundError("Chat", str(chat_id))

        character = await self._characters.get_by_id(chat.character_id)
        if not character:
            raise NotFoundError("Character", str(chat.character_id))

        scenario = None
        if chat.scenario_id:
            scenario = chat.scenario or await self._scenarios.get_by_id(chat.scenario_id)

        await self._payments.deduct_gems(
            user_id,
            character.message_price,
            f"Message to {character.name}",
            reference_id=str(chat_id),
        )

        await self._chats.add_message(chat_id, "user", content)

        history = await self._chats.get_messages(chat_id, limit=self.MAX_CONTEXT_MESSAGES)
        ai_messages = [ChatMessage(role=m.role.value, content=m.content) for m in history]

        from app.providers.ai.base import ChatCompletionRequest

        response = await self._ai.complete(
            ChatCompletionRequest(
                messages=ai_messages,
                system_prompt=self._build_system_prompt(character, scenario),
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
        items = [await self._to_list_item(chat) for chat in chats]
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

    async def _require_user_chat(self, user_id: UUID, chat_id: UUID) -> Chat:
        chat = await self._chats.get_by_id(chat_id)
        if not chat or chat.user_id != user_id or chat.status != ChatStatus.ACTIVE:
            raise NotFoundError("Chat", str(chat_id))
        return chat

    def _build_system_prompt(self, character, scenario: CharacterScenario | None) -> str:
        parts: list[str] = []
        if character.personality_prompt:
            parts.append(character.personality_prompt.strip())
        if scenario:
            if scenario.story:
                parts.append(f"Сценарий «{scenario.title}»:\n{scenario.story.strip()}")
            if scenario.communication_style:
                parts.append(f"Стиль общения: {scenario.communication_style.strip()}")
        return "\n\n".join(parts) if parts else "You are a helpful assistant."

    def _display_title(self, chat: Chat, character_name: str, scenario_title: str | None) -> str:
        if chat.custom_title:
            return chat.custom_title.strip()
        if scenario_title:
            return f"{character_name} · {scenario_title}"
        return character_name

    def _to_chat_response(
        self, chat: Chat, character, scenario: CharacterScenario | None
    ) -> ChatResponse:
        name = character.name if character else "Персонаж"
        scenario_title = scenario.title if scenario else None
        return ChatResponse(
            id=chat.id,
            character_id=chat.character_id,
            scenario_id=chat.scenario_id,
            character_name=name,
            scenario_title=scenario_title,
            character_avatar_url=character.avatar_url if character else None,
            status=chat.status.value if hasattr(chat.status, "value") else str(chat.status),
            message_count=chat.message_count,
            last_message_at=chat.last_message_at,
            created_at=chat.created_at,
        )

    async def _to_list_item(self, chat: Chat) -> ChatListResponse:
        character = chat.character or await self._characters.get_by_id(chat.character_id)
        scenario = chat.scenario
        if chat.scenario_id and not scenario:
            scenario = await self._scenarios.get_by_id(chat.scenario_id)
        name = character.name if character else "Персонаж"
        scenario_title = scenario.title if scenario else None
        preview = await self._chats.get_last_message_preview(chat.id)
        return ChatListResponse(
            id=chat.id,
            character_id=chat.character_id,
            scenario_id=chat.scenario_id,
            scenario_title=scenario_title,
            character_name=name,
            character_avatar_url=character.avatar_url if character else None,
            display_title=self._display_title(chat, name, scenario_title),
            is_pinned=chat.is_pinned,
            last_message_preview=preview,
            last_message_at=chat.last_message_at,
            message_count=chat.message_count,
        )
