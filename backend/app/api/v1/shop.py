from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.catalog import ShopProductResponse
from app.services.catalog_service import CatalogService

router = APIRouter()


@router.get("/products", response_model=list[ShopProductResponse])
async def list_shop_products(session: AsyncSession = Depends(get_db)):
    service = CatalogService(session)
    return await service.list_products_public()
