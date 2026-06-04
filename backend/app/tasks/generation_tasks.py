import asyncio
import uuid
from uuid import UUID

import httpx
from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


def _image_media_type(content_type: str | None, data: bytes) -> tuple[str, str]:
    normalized = (content_type or "").split(";", 1)[0].strip().lower()
    if normalized in {"image/jpeg", "image/jpg"}:
        return "jpg", "image/jpeg"
    if normalized == "image/png":
        return "png", "image/png"
    if normalized == "image/webp":
        return "webp", "image/webp"

    if data.startswith(b"\xff\xd8\xff"):
        return "jpg", "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp", "image/webp"

    raise ValueError(f"Generated image response is not a supported image type: {content_type or 'unknown'}")


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_image_generation(self, generation_id: str):
    """Process image generation via Celery worker — NOT through FastAPI."""
    logger.info("Processing generation %s", generation_id)

    async def _process():
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from app.core.config import get_settings
        from app.models import GenerationStatus
        from app.providers.ai.image_base import ImageGenerationRequest
        from app.providers.factory import get_image_provider, get_storage_provider
        from app.providers.storage.base import StorageBucket
        from app.repositories.generation_repository import GenerationRepository

        settings = get_settings()
        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            repo = GenerationRepository(session)
            generation = await repo.get_by_id(UUID(generation_id))
            if not generation:
                logger.error("Generation %s not found", generation_id)
                return

            await repo.update_status(generation, GenerationStatus.PROCESSING)

            try:
                image_provider = get_image_provider()
                storage = get_storage_provider()

                meta = generation.metadata_ or {}
                result = await image_provider.generate(
                    ImageGenerationRequest(
                        prompt=generation.prompt,
                        negative_prompt=generation.negative_prompt or "",
                        model=generation.model_id,
                        width=int(meta.get("width") or 1024),
                        height=int(meta.get("height") or 1024),
                    )
                )

                async with httpx.AsyncClient(follow_redirects=True) as client:
                    img_response = await client.get(result.image_url, timeout=60.0)
                    img_response.raise_for_status()
                    image_data = img_response.content
                    extension, content_type = _image_media_type(
                        img_response.headers.get("content-type"),
                        image_data,
                    )

                key = f"{generation.user_id}/{generation_id}.{extension}"
                upload = await storage.upload(
                    StorageBucket.GENERATIONS, key, image_data, content_type
                )

                await repo.update_status(
                    generation,
                    GenerationStatus.COMPLETED,
                    image_url=upload.url,
                    provider=result.provider,
                )
                generation.error_message = None
                await session.commit()
                logger.info(
                    "Generation %s completed model_name=%s model_id=%s provider=%s",
                    generation_id,
                    result.metadata.get("model_name") or generation.model_id or "default",
                    result.metadata.get("requested_model") or generation.model_id,
                    result.provider,
                )

            except Exception as exc:
                logger.exception("Generation %s failed", generation_id)
                await repo.update_status(
                    generation,
                    GenerationStatus.FAILED,
                    error_message=str(exc),
                )
                await session.commit()
                if isinstance(exc, ValueError):
                    return
                raise self.retry(exc=exc) from exc

    run_async(_process())
