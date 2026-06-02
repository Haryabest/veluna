from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.catalog import HomeArtResponse
from app.services.catalog_service import CatalogService

router = APIRouter()


@router.get("", response_model=list[HomeArtResponse])
async def list_home_arts(session: AsyncSession = Depends(get_db)):
    return await CatalogService(session).list_home_arts_public()
