from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas import CharacterDetailResponse, CharacterScenarioResponse, PaginatedResponse
from app.services.character_service import CharacterService

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_characters(
    page: int = Query(1, ge=1),
    category: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    service = CharacterService(session)
    return await service.list_characters(page=page, category=category)


@router.get("/{character_id}/scenarios", response_model=list[CharacterScenarioResponse])
async def list_character_scenarios(character_id: UUID, session: AsyncSession = Depends(get_db)):
    service = CharacterService(session)
    return await service.list_scenarios(character_id)


@router.get("/{character_id}", response_model=CharacterDetailResponse)
async def get_character(character_id: UUID, session: AsyncSession = Depends(get_db)):
    service = CharacterService(session)
    return await service.get_character(character_id)


@router.get("/slug/{slug}", response_model=CharacterDetailResponse)
async def get_character_by_slug(slug: str, session: AsyncSession = Depends(get_db)):
    service = CharacterService(session)
    return await service.get_by_slug(slug)
