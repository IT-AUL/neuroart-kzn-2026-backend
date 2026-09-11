from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.ai import (
    ApproveContentRequest,
    GenerateLocationContentRequest,
    GenerateLocationContentResponse,
)
from app.schemas.location import (
    LocationCreateRequest,
    LocationResponse,
    LocationUpdateRequest,
)
from app.services.location_service import LocationService
from app.services.yandex_llm_service import yandex_llm_service

router = APIRouter(prefix="/locations", tags=["Locations"])


# ============================================================================
# Editor & AI HITL Endpoints (Must precede /{id} parameter routes)
# ============================================================================

@router.post(
    "/editor/generate-content",
    response_model=GenerateLocationContentResponse,
    summary="HITL: Generate creative lore and description options using Yandex LLM",
    description=(
        "Takes a location title and optional theme context, returning multiple candidate sets "
        "of layers (layer1, layer2), action hints, character dialogue lines, easter eggs, and artifact suggestions. "
        "Allows a human content editor to review, edit, and choose the best option before saving to DB."
    ),
)
async def generate_location_content(
    payload: GenerateLocationContentRequest,
) -> GenerateLocationContentResponse:
    return await yandex_llm_service.generate_location_variants(
        title=payload.title,
        context=payload.context_or_theme,
        count=payload.variant_count,
    )


@router.post(
    "/{id}/editor/approve-content",
    response_model=LocationResponse,
    summary="HITL: Approve and apply selected/edited AI content to a location",
    description=(
        "Applies approved or manually tweaked content fields directly to the location record "
        "in the database and returns the updated location."
    ),
)
async def approve_location_content(
    id: str,
    payload: ApproveContentRequest,
    db: AsyncSession = Depends(get_db),
) -> LocationResponse:
    service = LocationService(db)
    return await service.apply_approved_content(location_id=id, payload=payload)


# ============================================================================
# Core Location CRUD Endpoints
# ============================================================================

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


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new route location (Editor)",
    description="Creates a new location with 3D models, texts, coordinates, and mechanics configuration.",
)
async def create_location(
    payload: LocationCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> LocationResponse:
    service = LocationService(db)
    return await service.create_location(payload=payload)


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


@router.put(
    "/{id}",
    response_model=LocationResponse,
    summary="Update a route location (Editor)",
    description="Updates existing location properties, texts, model references, or mechanics parameters.",
)
async def update_location(
    id: str,
    payload: LocationUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> LocationResponse:
    service = LocationService(db)
    return await service.update_location(location_id=id, payload=payload)


@router.delete(
    "/{id}",
    summary="Delete a route location (Editor)",
    description="Deletes a location and cleans up its session progress entries.",
)
async def delete_location(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    service = LocationService(db)
    await service.delete_location(location_id=id)
    return {"status": "deleted", "id": id}
