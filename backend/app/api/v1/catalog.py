from fastapi import APIRouter
from pydantic import BaseModel

from app.services.catalog_version_service import get_catalog_version

router = APIRouter()


class CatalogVersionResponse(BaseModel):
    version: int


@router.get("/version", response_model=CatalogVersionResponse)
async def catalog_version() -> CatalogVersionResponse:
    return CatalogVersionResponse(version=await get_catalog_version())
