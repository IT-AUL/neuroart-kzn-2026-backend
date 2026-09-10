from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import LocationNotFoundError
from app.db.base import utc_now
from app.db.models.location import Location
from app.db.models.progress import UserProgress
from app.schemas.passport import PassportArtifactItem, PassportResponse
from app.schemas.progress import ProgressResponse
from app.services.mechanics import get_mechanic_validator


class PassportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_progress(
        self,
        session_id: str,
        location_id: str,
        submission_data: Optional[Dict[str, Any]] = None,
    ) -> ProgressResponse:
        """
        Record completion of a location for a session.
        1. Checks idempotency (if already completed, returns existing record).
        2. Validates mechanic business logic (trace contour or tap_climb dynamics).
        3. Awards location artifact to session passport.
        """
        # 1. Verify location exists
        loc_stmt = select(Location).where(Location.id == location_id)
        loc_result = await self.session.execute(loc_stmt)
        location = loc_result.scalar_one_or_none()
        if not location:
            raise LocationNotFoundError(location_id=location_id)

        # 2. Check if progress already recorded for this session and location (idempotency)
        prog_stmt = select(UserProgress).where(
            UserProgress.session_id == session_id,
            UserProgress.location_id == location_id,
        )
        prog_result = await self.session.execute(prog_stmt)
        existing_progress = prog_result.scalar_one_or_none()

        if existing_progress:
            return ProgressResponse(
                session_id=session_id,
                location_id=location_id,
                is_new_unlock=False,
                artifact=existing_progress.artifact_data,
                unlocked_at=existing_progress.unlocked_at,
                message="Location was already completed. Artifact previously unlocked.",
            )

        # 3. Business logic validation for mechanics: trace, tap_climb, none
        validator = get_mechanic_validator(location.mechanic)
        validation_result = validator.validate(
            mechanic_params=location.mechanic_params,
            submission_data=submission_data,
        )

        if not validation_result.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": f"Mechanic '{location.mechanic}' validation failed",
                    "message": validation_result.message,
                    "score": validation_result.score,
                    "details": validation_result.details,
                },
            )

        # 4. Create new progress entry and store unlocked artifact
        artifact_data = location.artifact
        new_progress = UserProgress(
            session_id=session_id,
            location_id=location_id,
            artifact_data=artifact_data,
            unlocked_at=utc_now(),
        )
        self.session.add(new_progress)
        await self.session.commit()
        await self.session.refresh(new_progress)

        return ProgressResponse(
            session_id=session_id,
            location_id=location_id,
            is_new_unlock=True,
            artifact=new_progress.artifact_data,
            unlocked_at=new_progress.unlocked_at,
            message="Location completed successfully! Artifact unlocked.",
            validation=validation_result,
        )

    async def get_passport(self, session_id: str) -> PassportResponse:
        """
        Retrieve passport state for a session.
        """
        stmt = (
            select(UserProgress)
            .where(UserProgress.session_id == session_id)
            .order_by(UserProgress.unlocked_at.asc())
        )
        result = await self.session.execute(stmt)
        progress_entries = list(result.scalars().all())

        collected_artifacts: List[PassportArtifactItem] = []
        for entry in progress_entries:
            art = entry.artifact_data
            collected_artifacts.append(
                PassportArtifactItem(
                    id=art.get("id", ""),
                    name=art.get("name", ""),
                    icon=art.get("icon", ""),
                    location_id=entry.location_id,
                    unlocked_at=entry.unlocked_at,
                )
            )

        return PassportResponse(
            session_id=session_id,
            total_slots=settings.PASSPORT_TOTAL_SLOTS,
            collected_count=len(collected_artifacts),
            artifacts=collected_artifacts,
        )
