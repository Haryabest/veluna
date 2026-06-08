import logging
import threading
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ServiceUnavailableError, ValidationError
from app.models import AiReplyStatus, CharacterNarrator, CharacterScenario, Chat, ChatStatus, Message, MessageRole
from app.providers.factory import get_chat_provider
from app.repositories.character_narrator_repository import CharacterNarratorRepository
from app.repositories.character_repository import CharacterRepository
from app.repositories.character_scenario_repository import CharacterScenarioRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.generation_repository import PaymentRepository
from app.schemas import (
    ChatListResponse,
    ChatResponse,
    MessageDeleteResponse,
    MessageReplyPreview,
    MessageResponse,
    SendMessageResponse,
)
from app.services.chat_prompt import build_character_system_prompt

logger = logging.getLogger(__name__)


class ChatService:
    MAX_CONTEXT_MESSAGES = 20

    @staticmethod
    def message_heart_cost(narrator: CharacterNarrator | None) -> int:
        if narrator and narrator.price > 0:
            return narrator.price
        return 1

    def __init__(self, session: AsyncSession):
        self._session = session
        self._chats = ChatRepository(session)
        self._characters = CharacterRepository(session)
        self._scenarios = CharacterScenarioRepository(session)
        self._narrators = CharacterNarratorRepository(session)
        self._payments = PaymentRepository(session)
        self._ai = get_chat_provider()

    async def get_or_create_chat(
        self, user_id: UUID, character_id: UUID, scenario_id: UUID, narrator_id: UUID
    ) -> ChatResponse:
        character = await self._characters.get_by_id(character_id)
        if not character or not character.is_active:
            raise NotFoundError("Character", str(character_id))

        scenario = await self._scenarios.get_by_id(scenario_id)
        if not scenario or scenario.character_id != character_id or not scenario.is_active:
            raise NotFoundError("Scenario", str(scenario_id))

        narrator = await self._narrators.get_by_id(narrator_id)
        if not narrator or narrator.character_id != character_id or not narrator.is_active:
            raise NotFoundError("Narrator", str(narrator_id))

        chat = await self._chats.get_user_chat(user_id, character_id, scenario_id, narrator_id)
        if not chat:
            chat = await self._chats.create(user_id, character_id, scenario_id, narrator_id)
            opening = (scenario.opening_message or "").strip() or (character.greeting_message or "").strip()
            if opening:
                await self._chats.add_message(chat.id, MessageRole.ASSISTANT, opening)
            chat = await self._chats.get_by_id(chat.id)

        return self._to_chat_response(chat, character, scenario, narrator)

    async def get_chat(self, user_id: UUID, chat_id: UUID) -> ChatResponse:
        chat = await self._require_user_chat(user_id, chat_id)
        character = chat.character or await self._characters.get_by_id(chat.character_id)
        scenario = chat.scenario
        if chat.scenario_id and not scenario:
            scenario = await self._scenarios.get_by_id(chat.scenario_id)
        narrator = chat.narrator
        if chat.narrator_id and not narrator:
            narrator = await self._narrators.get_by_id(chat.narrator_id)
        return self._to_chat_response(chat, character, scenario, narrator)

    async def switch_scenario(self, user_id: UUID, chat_id: UUID, scenario_id: UUID) -> ChatResponse:
        chat = await self._require_user_chat(user_id, chat_id)
        if chat.scenario_id == scenario_id:
            return await self.get_chat(user_id, chat_id)

        scenario = await self._scenarios.get_by_id(scenario_id)
        if not scenario or scenario.character_id != chat.character_id or not scenario.is_active:
            raise NotFoundError("Scenario", str(scenario_id))

        chat.scenario_id = scenario_id
        await self._chats.add_message(
            chat_id,
            MessageRole.SYSTEM,
            f"Вы сменили сценарий на «{scenario.title}»",
        )
        await self._session.flush()
        character = chat.character or await self._characters.get_by_id(chat.character_id)
        narrator = chat.narrator
        if chat.narrator_id and not narrator:
            narrator = await self._narrators.get_by_id(chat.narrator_id)
        return self._to_chat_response(chat, character, scenario, narrator)

    async def switch_narrator(self, user_id: UUID, chat_id: UUID, narrator_id: UUID) -> ChatResponse:
        chat = await self._require_user_chat(user_id, chat_id)
        if chat.narrator_id == narrator_id:
            return await self.get_chat(user_id, chat_id)

        narrator = await self._narrators.get_by_id(narrator_id)
        if not narrator or narrator.character_id != chat.character_id or not narrator.is_active:
            raise NotFoundError("Narrator", str(narrator_id))

        chat.narrator_id = narrator_id
        await self._chats.add_message(
            chat_id,
            MessageRole.SYSTEM,
            f"Вы сменили рассказчика на «{narrator.name}»",
        )
        await self._session.flush()
        character = chat.character or await self._characters.get_by_id(chat.character_id)
        scenario = chat.scenario
        if chat.scenario_id and not scenario:
            scenario = await self._scenarios.get_by_id(chat.scenario_id)
        return self._to_chat_response(chat, character, scenario, narrator)

    async def send_message(
        self,
        user_id: UUID,
        chat_id: UUID,
        content: str,
        reply_to_id: UUID | None = None,
    ) -> SendMessageResponse:
        chat = await self._chats.get_by_id(chat_id)
        if not chat or chat.user_id != user_id:
            raise NotFoundError("Chat", str(chat_id))

        if chat.ai_reply_status == AiReplyStatus.PROCESSING.value:
            raise ValidationError("Дождитесь ответа персонажа")

        character = await self._characters.get_by_id(chat.character_id)
        if not character:
            raise NotFoundError("Character", str(chat.character_id))

        if reply_to_id:
            parent = await self._chats.get_message(reply_to_id, chat_id)
            if not parent or parent.deleted_for_all:
                raise NotFoundError("Message", str(reply_to_id))

        narrator = chat.narrator
        if chat.narrator_id and not narrator:
            narrator = await self._narrators.get_by_id(chat.narrator_id)

        heart_cost = self.message_heart_cost(narrator)
        if self._ai.provider_name != "stub" and heart_cost > 0:
            balance = await self._payments.get_balance(user_id)
            available = balance.credits if balance else 0
            if available < heart_cost:
                from app.core.exceptions import InsufficientBalanceError

                raise InsufficientBalanceError(required=heart_cost, available=available, currency="credits")

        await self._chats.add_message(
            chat_id,
            MessageRole.USER,
            content,
            reply_to_id=reply_to_id,
        )
        await self._chats.set_ai_reply_status(chat, AiReplyStatus.PROCESSING, error=None)

        user_msg = await self._chats.get_latest_message(chat_id)
        if not user_msg:
            raise NotFoundError("Message", "last")

        self._enqueue_ai_response(chat_id, user_msg.id, user_id)

        return SendMessageResponse(
            user_message=self._to_message_response(user_msg),
            ai_reply_status=AiReplyStatus.PROCESSING.value,
        )

    async def attach_generation(
        self, user_id: UUID, chat_id: UUID, generation_id: UUID
    ) -> MessageResponse:
        from app.models import GenerationStatus
        from app.repositories.generation_repository import GenerationRepository

        chat = await self._chats.get_by_id(chat_id)
        if not chat or chat.user_id != user_id:
            raise NotFoundError("Chat", str(chat_id))

        generations = GenerationRepository(self._session)
        generation = await generations.get_by_id(generation_id)
        if not generation or generation.user_id != user_id:
            raise NotFoundError("Generation", str(generation_id))
        if generation.status != GenerationStatus.COMPLETED:
            raise ValidationError("Арт ещё не готов")
        if not generation.image_url:
            raise ValidationError("Нет изображения")

        prompt = (generation.prompt or "Арт").strip()
        content = f"![{prompt}]({generation.image_url})"
        await self._chats.add_message(chat_id, MessageRole.ASSISTANT, content)
        message = await self._chats.get_latest_message(chat_id)
        if not message:
            raise NotFoundError("Message", "last")
        return self._to_message_response(message)

    def _enqueue_ai_response(self, chat_id: UUID, user_message_id: UUID, user_id: UUID) -> None:
        from app.tasks.chat_tasks import process_ai_response

        cid, mid, uid = str(chat_id), str(user_message_id), str(user_id)
        try:
            process_ai_response.delay(cid, mid, uid)
        except Exception as exc:
            settings = get_settings()
            if settings.app_env != "development":
                logger.exception("Failed to enqueue AI response for chat %s", cid)
                raise ServiceUnavailableError(
                    "Очередь чата недоступна. Запустите Redis и worker: "
                    "celery -A app.workers.celery_app worker -Q chat_queue"
                ) from exc

            logger.warning("Celery unavailable for chat %s — running AI inline (dev)", cid)

            def _run_inline() -> None:
                try:
                    process_ai_response.apply(args=[cid, mid, uid])
                except Exception:
                    logger.exception("Inline AI response failed for chat %s", cid)

            threading.Thread(target=_run_inline, daemon=True).start()

    async def delete_message(
        self,
        user_id: UUID,
        chat_id: UUID,
        message_id: UUID,
        scope: str,
    ) -> MessageDeleteResponse:
        chat = await self._chats.get_by_id(chat_id)
        if not chat or chat.user_id != user_id:
            raise NotFoundError("Chat", str(chat_id))

        message = await self._chats.get_message(message_id, chat_id)
        if not message or message.deleted_for_all:
            raise NotFoundError("Message", str(message_id))

        if message.role == MessageRole.SYSTEM:
            raise ValidationError("Системные сообщения нельзя удалить")

        if scope == "self":
            await self._chats.hide_message_for_user(message, user_id)
        elif scope == "all":
            await self._chats.delete_message_for_all(message)
        else:
            raise ValidationError("scope должен быть self или all")

        return MessageDeleteResponse(id=message_id, scope=scope)

    async def get_messages(self, user_id: UUID, chat_id: UUID, limit: int = 50) -> list[MessageResponse]:
        chat = await self._chats.get_by_id(chat_id)
        if not chat or chat.user_id != user_id:
            raise NotFoundError("Chat", str(chat_id))

        messages = await self._chats.get_messages(chat_id, user_id, limit=limit)
        return [self._to_message_response(m) for m in messages]

    def _to_message_response(self, message: Message) -> MessageResponse:
        preview = None
        if message.reply_to and not message.reply_to.deleted_for_all:
            preview = MessageReplyPreview(
                id=message.reply_to.id,
                role=message.reply_to.role.value,
                content=message.reply_to.content[:200],
            )
        return MessageResponse(
            id=message.id,
            chat_id=message.chat_id,
            role=message.role.value,
            content=message.content,
            tokens_used=message.tokens_used,
            is_regenerated=message.is_regenerated,
            reply_to_id=message.reply_to_id,
            reply_preview=preview,
            created_at=message.created_at,
        )

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

    def _build_system_prompt(
        self,
        character,
        scenario: CharacterScenario | None,
        narrator: CharacterNarrator | None,
    ) -> str:
        return build_character_system_prompt(character, scenario, narrator)

    def _display_title(
        self, chat: Chat, character_name: str, scenario_title: str | None, narrator_name: str | None
    ) -> str:
        if chat.custom_title:
            return chat.custom_title.strip()
        if scenario_title and narrator_name:
            return f"{character_name} · {scenario_title} · {narrator_name}"
        if scenario_title:
            return f"{character_name} · {scenario_title}"
        return character_name

    def _to_chat_response(
        self,
        chat: Chat,
        character,
        scenario: CharacterScenario | None,
        narrator: CharacterNarrator | None,
    ) -> ChatResponse:
        name = character.name if character else "Персонаж"
        scenario_title = scenario.title if scenario else None
        narrator_name = narrator.name if narrator else None
        return ChatResponse(
            id=chat.id,
            character_id=chat.character_id,
            scenario_id=chat.scenario_id,
            narrator_id=chat.narrator_id,
            character_name=name,
            scenario_title=scenario_title,
            narrator_name=narrator_name,
            character_avatar_url=character.avatar_url if character else None,
            status=chat.status.value if hasattr(chat.status, "value") else str(chat.status),
            message_count=chat.message_count,
            last_message_at=chat.last_message_at,
            ai_reply_status=chat.ai_reply_status or AiReplyStatus.IDLE.value,
            ai_reply_error=chat.ai_reply_error,
            message_heart_cost=self.message_heart_cost(narrator),
            created_at=chat.created_at,
        )

    async def _to_list_item(self, chat: Chat) -> ChatListResponse:
        character = chat.character or await self._characters.get_by_id(chat.character_id)
        scenario = chat.scenario
        if chat.scenario_id and not scenario:
            scenario = await self._scenarios.get_by_id(chat.scenario_id)
        narrator = chat.narrator
        if chat.narrator_id and not narrator:
            narrator = await self._narrators.get_by_id(chat.narrator_id)
        name = character.name if character else "Персонаж"
        scenario_title = scenario.title if scenario else None
        narrator_name = narrator.name if narrator else None
        preview = await self._chats.get_last_message_preview(chat.id, chat.user_id)
        return ChatListResponse(
            id=chat.id,
            character_id=chat.character_id,
            scenario_id=chat.scenario_id,
            scenario_title=scenario_title,
            narrator_id=chat.narrator_id,
            narrator_name=narrator_name,
            character_name=name,
            character_avatar_url=character.avatar_url if character else None,
            display_title=self._display_title(chat, name, scenario_title, narrator_name),
            is_pinned=chat.is_pinned,
            last_message_preview=preview,
            last_message_at=chat.last_message_at,
            message_count=chat.message_count,
        )
