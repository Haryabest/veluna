from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.services.platform_settings_service import PlatformSettingsService
from app.models import GenerationStatus
from app.repositories.character_repository import CharacterRepository
from app.repositories.generation_repository import GenerationRepository, PaymentRepository
from app.schemas import GenerationCreate, GenerationResponse


class GenerationService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._generations = GenerationRepository(session)
        self._characters = CharacterRepository(session)
        self._payments = PaymentRepository(session)
        self._platform = PlatformSettingsService()

    async def create_generation(self, user_id: UUID, data: GenerationCreate) -> GenerationResponse:
        pricing = await self._platform.get_pricing()
        gems_cost = pricing.gem_cost_per_generation

        if data.character_id:
            character = await self._characters.get_by_id(data.character_id)
            if not character:
                raise NotFoundError("Character", str(data.character_id))
            gems_cost = character.generation_price

        await self._payments.deduct_gems(
            user_id,
            gems_cost,
            "Image generation",
        )

        generation = await self._generations.create(
            user_id=user_id,
            character_id=data.character_id,
            prompt=data.prompt,
            negative_prompt=data.negative_prompt,
            gems_cost=gems_cost,
            status=GenerationStatus.PENDING,
        )

        from app.tasks.generation_tasks import process_image_generation
        task = process_image_generation.delay(str(generation.id))
        await self._generations.update_status(generation, GenerationStatus.PENDING, task_id=task.id)

        return GenerationResponse.model_validate(generation)

    async def get_generation(self, user_id: UUID, generation_id: UUID) -> GenerationResponse:
        generation = await self._generations.get_by_id(generation_id)
        if not generation or generation.user_id != user_id:
            raise NotFoundError("Generation", str(generation_id))
        return GenerationResponse.model_validate(generation)

    async def list_user_generations(self, user_id: UUID, page: int = 1) -> tuple[list[GenerationResponse], int]:
        generations, total = await self._generations.list_user_generations(user_id, page=page)
        return [GenerationResponse.model_validate(g) for g in generations], total
