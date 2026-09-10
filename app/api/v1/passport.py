from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_session_id
from app.core.database import get_db
from app.schemas.passport import PassportResponse
from app.services.passport_service import PassportService

router = APIRouter(prefix="/passport", tags=["Passport"])


@router.get(
    "",
    response_model=PassportResponse,
    summary="Get session passport state",
    description=(
        "Returns the current state of the session passport: list of collected artifacts, "
        "total slots (10 for demo), and collected count. Requires X-Session-ID header."
    ),
)
async def get_passport(
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
) -> PassportResponse:
    service = PassportService(db)
    return await service.get_passport(session_id=session_id)
