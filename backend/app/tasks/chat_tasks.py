import asyncio
from uuid import UUID

from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task
def process_chat_analytics(user_id: str, chat_id: str, tokens_used: int):
    from app.tasks.analytics_tasks import track_event

    track_event.delay(user_id, "chat_message", {"chat_id": chat_id, "tokens_used": tokens_used})
    logger.info("Chat analytics: user=%s chat=%s tokens=%d", user_id, chat_id, tokens_used)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=15)
def process_ai_response(self, chat_id: str, user_message_id: str, user_id: str):
    """Generate assistant reply in background after user message is saved."""

    async def _process():
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from app.core.config import get_settings
        from app.models import AiReplyStatus, MessageRole
        from app.providers.ai.base import ChatCompletionRequest, ChatMessage
        from app.providers.factory import get_chat_provider
        from app.repositories.character_narrator_repository import CharacterNarratorRepository
        from app.repositories.character_repository import CharacterRepository
        from app.repositories.character_scenario_repository import CharacterScenarioRepository
        from app.repositories.chat_repository import ChatRepository
        from app.repositories.generation_repository import PaymentRepository
        from app.services.chat_service import ChatService

        settings = get_settings()
        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            chats = ChatRepository(session)
            characters = CharacterRepository(session)
            scenarios = CharacterScenarioRepository(session)
            narrators = CharacterNarratorRepository(session)
            ai = get_chat_provider()

            chat = await chats.get_by_id(UUID(chat_id))
            if not chat:
                logger.error("Chat %s not found", chat_id)
                return

            user_msg = await chats.get_message(UUID(user_message_id), UUID(chat_id))
            if not user_msg:
                logger.error("User message %s not found in chat %s", user_message_id, chat_id)
                await chats.set_ai_reply_status(chat, AiReplyStatus.FAILED, "Сообщение не найдено")
                await session.commit()
                return

            character = await characters.get_by_id(chat.character_id)
            if not character:
                await chats.set_ai_reply_status(chat, AiReplyStatus.FAILED, "Персонаж не найден")
                await session.commit()
                return

            scenario = chat.scenario
            if chat.scenario_id and not scenario:
                scenario = await scenarios.get_by_id(chat.scenario_id)

            narrator = chat.narrator
            if chat.narrator_id and not narrator:
                narrator = await narrators.get_by_id(chat.narrator_id)

            try:
                history = await chats.get_messages(UUID(chat_id), UUID(user_id), limit=ChatService.MAX_CONTEXT_MESSAGES)
                ai_messages = [
                    ChatMessage(role=m.role.value, content=m.content)
                    for m in history
                    if m.role != MessageRole.SYSTEM
                ]

                response = await ai.complete(
                    ChatCompletionRequest(
                        messages=ai_messages,
                        system_prompt=ChatService(session)._build_system_prompt(character, scenario, narrator),
                    )
                )

                from app.services.api_cost_service import build_chat_message_api_meta

                msg_meta = build_chat_message_api_meta(response)
                await chats.add_message(
                    UUID(chat_id),
                    MessageRole.ASSISTANT,
                    response.content,
                    tokens_used=response.tokens_used,
                    metadata_=msg_meta,
                )

                heart_cost = ChatService.message_heart_cost(narrator)
                if heart_cost > 0 and ai.provider_name != "stub":
                    payments = PaymentRepository(session)
                    await payments.deduct_credits(
                        UUID(user_id),
                        heart_cost,
                        f"Сообщение в чате: {character.name}",
                        reference_id=chat_id,
                        extra_metadata={"api_cost_rub": msg_meta.get("api_cost_rub")},
                    )

                await chats.set_ai_reply_status(chat, AiReplyStatus.IDLE, error=None)
                await session.commit()

                try:
                    from app.services.chat_cache_service import chat_cache

                    await chat_cache.invalidate_chat(UUID(chat_id), UUID(user_id))
                    await chat_cache.invalidate_user_lists(UUID(user_id))
                except Exception:
                    logger.debug("Chat cache invalidation failed after AI reply", exc_info=True)

                try:
                    process_chat_analytics.delay(user_id, chat_id, response.tokens_used)
                except Exception:
                    pass

                logger.info("AI response completed for chat %s", chat_id)

            except Exception as exc:
                logger.exception("AI response failed for chat %s", chat_id)
                await chats.set_ai_reply_status(chat, AiReplyStatus.FAILED, str(exc))
                await session.commit()
                try:
                    from app.services.chat_cache_service import chat_cache

                    await chat_cache.invalidate_chat(UUID(chat_id), UUID(user_id))
                except Exception:
                    logger.debug("Chat cache invalidation failed after AI error", exc_info=True)
                raise self.retry(exc=exc) from exc

    run_async(_process())
