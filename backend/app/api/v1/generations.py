from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.session import get_db
from app.providers.factory import get_chat_provider
from app.schemas import GenerationCreate, GenerationResponse, PaginatedResponse, UserResponse
from app.services.generation_service import GenerationService

router = APIRouter()


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class TranslateResponse(BaseModel):
    translated: str


@router.post("/translate", response_model=TranslateResponse)
async def translate_prompt(
    data: TranslateRequest,
    user: UserResponse = Depends(get_current_user),
):
    provider = get_chat_provider()
    system = "You are a translator. Translate the following Russian text to English. Output ONLY the translation, nothing else."
    result = await provider.chat([
        {"role": "system", "content": system},
        {"role": "user", "content": data.text},
    ])
    return TranslateResponse(translated=result.strip())


@router.post("", response_model=GenerationResponse, status_code=202)
async def create_generation(
    data: GenerationCreate,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = GenerationService(session)
    return await service.create_generation(user.id, data)


@router.get("/{generation_id}", response_model=GenerationResponse)
async def get_generation(
    generation_id: UUID,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = GenerationService(session)
    return await service.get_generation(user.id, generation_id)


@router.get("", response_model=PaginatedResponse)
async def list_generations(
    page: int = Query(1, ge=1),
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = GenerationService(session)
    generations, total = await service.list_user_generations(user.id, page=page)
    page_size = 20
    return PaginatedResponse(
        items=generations, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )
