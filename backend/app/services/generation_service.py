import logging
import threading
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ServiceUnavailableError, ValidationError
from app.providers.factory import get_image_provider
from app.services.platform_settings_service import PlatformSettingsService
from app.models import GenerationStatus
from app.repositories.character_repository import CharacterRepository
from app.repositories.generation_repository import GenerationRepository, PaymentRepository
from app.schemas import GenerationCreate, GenerationResponse

logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._generations = GenerationRepository(session)
        self._characters = CharacterRepository(session)
        self._payments = PaymentRepository(session)
        self._platform = PlatformSettingsService()

    async def create_generation(self, user_id: UUID, data: GenerationCreate) -> GenerationResponse:
        settings = get_settings()
        image_provider = get_image_provider()
        if image_provider.provider_name == "civitai" and not settings.civitai_api_key.strip():
            raise ValidationError(
                "Добавьте CIVITAI_API_KEY в .env (Orchestration API: https://developer.civitai.com/site/)"
            )
        if image_provider.provider_name == "fal" and not settings.fal_api_key.strip():
            raise ValidationError("Добавьте FAL_API_KEY в .env")
        if image_provider.provider_name == "replicate" and not settings.replicate_api_token.strip():
            raise ValidationError("Добавьте REPLICATE_API_TOKEN в .env")
        if image_provider.provider_name == "zimage" and not settings.gen_api_key.strip():
            raise ValidationError(
                "Добавьте GEN_API_KEY в .env (Z-Image использует тот же токен, что и чат)"
            )

        # The frontend assembles the final English prompt from a per-style
        # template + the user's text, so we just use it as-is.
        prompt = data.prompt.strip()

        pricing = await self._platform.get_pricing()
        gems_cost = pricing.gem_cost_per_generation

        if data.character_id:
            character = await self._characters.get_by_id(data.character_id)
            if not character:
                raise NotFoundError("Character", str(data.character_id))
            gems_cost = character.generation_price

        balance = await self._payments.get_balance(user_id)
        available = balance.gems if balance else 0
        if available < gems_cost:
            from app.core.exceptions import InsufficientBalanceError

            raise InsufficientBalanceError(required=gems_cost, available=available)

        generation = await self._generations.create(
            user_id=user_id,
            character_id=data.character_id,
            prompt=prompt,
            negative_prompt=data.negative_prompt,
            model_id=data.model_id,
            gems_cost=gems_cost,
            status=GenerationStatus.PENDING,
            metadata_={
                "width": data.width,
                "height": data.height,
            },
        )

        from app.tasks.generation_tasks import process_image_generation

        gen_id = str(generation.id)
        task_id: str
        try:
            task = process_image_generation.delay(gen_id)
            task_id = task.id
        except Exception as exc:
            settings = get_settings()
            if settings.app_env != "development":
                logger.exception("Failed to enqueue generation %s", gen_id)
                raise ServiceUnavailableError(
                    "Очередь генерации недоступна. Запустите Redis и worker: "
                    "celery -A app.workers.celery_app worker -Q generation_queue"
                ) from exc

            logger.warning(
                "Celery broker unavailable for %s — running generation in background thread (dev)",
                gen_id,
            )
            task_id = f"inline-{gen_id}"

            def _run_inline() -> None:
                try:
                    process_image_generation.apply(args=[gen_id])
                except Exception:
                    logger.exception("Inline generation failed for %s", gen_id)

            threading.Thread(target=_run_inline, daemon=True).start()

        await self._generations.update_status(generation, GenerationStatus.PENDING, task_id=task_id)

        return GenerationResponse.model_validate(generation)

    async def get_generation(self, user_id: UUID, generation_id: UUID) -> GenerationResponse:
        generation = await self._generations.get_by_id(generation_id)
        if not generation or generation.user_id != user_id:
            raise NotFoundError("Generation", str(generation_id))
        return GenerationResponse.model_validate(generation)

    async def list_user_generations(self, user_id: UUID, page: int = 1) -> tuple[list[GenerationResponse], int]:
        generations, total = await self._generations.list_user_generations(user_id, page=page)
        return [GenerationResponse.model_validate(g) for g in generations], total
