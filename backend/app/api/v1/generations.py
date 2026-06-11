from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_flexible
from app.database.session import get_db
from app.models import GenerationStatus
from app.schemas import GenerationCreate, GenerationResponse, PaginatedResponse, UserResponse
from app.services.generation_service import GenerationService
from app.services.share_service import prepare_generation_share

router = APIRouter()


class GenerationShareResponse(BaseModel):
    prepared_message_id: str
    bot_link: str = ""


@router.post("", response_model=GenerationResponse, status_code=202)
async def create_generation(
    data: GenerationCreate,
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    service = GenerationService(session)
    return await service.create_generation(user.id, data)


@router.post("/{generation_id}/share", response_model=GenerationShareResponse)
async def share_generation(
    generation_id: UUID,
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    from app.core.exceptions import ValidationError

    service = GenerationService(session)
    generation = await service.get_generation(user.id, generation_id)
    if generation.status != GenerationStatus.COMPLETED.value:
        raise ValidationError("Арт ещё не готов")
    if not generation.image_url:
        raise ValidationError("Нет изображения для отправки")

    prepared_id, bot_link = await prepare_generation_share(
        telegram_user_id=user.telegram_id,
        image_url=generation.image_url,
    )
    return GenerationShareResponse(prepared_message_id=prepared_id, bot_link=bot_link)


@router.get("/{generation_id}", response_model=GenerationResponse)
async def get_generation(
    generation_id: UUID,
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    service = GenerationService(session)
    return await service.get_generation(user.id, generation_id)


@router.get("", response_model=PaginatedResponse)
async def list_generations(
    page: int = Query(1, ge=1),
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    service = GenerationService(session)
    generations, total = await service.list_user_generations(user.id, page=page)
    page_size = 20
    return PaginatedResponse(
        items=generations, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )
