from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_session_id
from app.core.database import get_db
from app.core.exceptions import LocationNotFoundError
from app.db.models.location import Location
from app.schemas.progress import ProgressResponse, ProgressSubmitRequest
from app.services.mechanics import MechanicValidationResult, get_mechanic_validator
from app.services.passport_service import PassportService

router = APIRouter(prefix="/progress", tags=["Progress & Mechanics"])


@router.post(
    "/{location_id}",
    response_model=ProgressResponse,
    summary="Record location completion, validate mechanic, and unlock artifact",
    description=(
        "Marks the location as completed for the current session and unlocks its artifact in the passport. "
        "Validates mechanic business logic (trace contour geometry, tap_climb physics & threshold). "
        "Idempotent: repeating the call for the same location does not duplicate the artifact."
    ),
)
async def submit_progress(
    location_id: str,
    payload: Optional[ProgressSubmitRequest] = None,
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
) -> ProgressResponse:
    service = PassportService(db)
    submission_dict = payload.to_submission_dict() if payload else None

    return await service.record_progress(
        session_id=session_id,
        location_id=location_id,
        submission_data=submission_dict,
    )


@router.post(
    "/verify/{location_id}",
    response_model=MechanicValidationResult,
    summary="Simulate and test mechanic execution without mutating database",
    description=(
        "Validates mechanic submission (trace drawn points against contour tolerance, or tap climb frequency and decay) "
        "and returns diagnostic simulation results without creating a progress record."
    ),
)
async def verify_mechanic_simulation(
    location_id: str,
    payload: Optional[ProgressSubmitRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> MechanicValidationResult:
    stmt = select(Location).where(Location.id == location_id)
    result = await db.execute(stmt)
    location = result.scalar_one_or_none()
    if not location:
        raise LocationNotFoundError(location_id=location_id)

    validator = get_mechanic_validator(location.mechanic)
    submission_dict = payload.to_submission_dict() if payload else None

    return validator.validate(
        mechanic_params=location.mechanic_params,
        submission_data=submission_dict,
    )
