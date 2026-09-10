from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.location import LocationResponse
from app.services.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get(
    "",
    response_model=List[LocationResponse],
    summary="Get all route locations with full configuration",
    description="Returns full list of route points. Frontend loads this once on application start.",
)
async def list_locations(
    db: AsyncSession = Depends(get_db),
) -> List[LocationResponse]:
    service = LocationService(db)
    return await service.get_all_locations()


@router.get(
    "/{id}",
    response_model=LocationResponse,
    summary="Get configuration of a single location",
    description="Returns detailed config of a single route point by its ID.",
)
async def get_location(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> LocationResponse:
    service = LocationService(db)
    return await service.get_location_by_id(location_id=id)
