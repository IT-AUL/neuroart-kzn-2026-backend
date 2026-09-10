from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.location import ArtifactSchema
from app.services.mechanics.base import MechanicValidationResult


class ProgressSubmitRequest(BaseModel):
    """Optional telemetry and mechanic verification payload."""
    # Common fields
    score: Optional[float] = Field(default=None, description="Reported score or percentage")
    
    # Trace mechanic fields
    user_path: Optional[List[Dict[str, float]]] = Field(
        default=None,
        description="Array of user finger coordinates [{'x': 0.1, 'y': 0.2}, ...]",
    )
    screen_width: Optional[float] = Field(
        default=None,
        description="Screen width in pixels for accurate tolerance calculation",
    )

    # Tap climb mechanic fields
    taps_count: Optional[int] = Field(
        default=None,
        description="Total number of taps performed during climb",
    )
    duration_seconds: Optional[float] = Field(
        default=None,
        description="Duration of the climbing attempt in seconds",
    )
    tap_timestamps: Optional[List[float]] = Field(
        default=None,
        description="Array of relative timestamps (in seconds) for each tap",
    )

    # Freeform / custom telemetry
    extra_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional game telemetry",
    )

    def to_submission_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        if self.score is not None:
            data["score"] = self.score
        if self.user_path is not None:
            data["user_path"] = self.user_path
        if self.screen_width is not None:
            data["screen_width"] = self.screen_width
        if self.taps_count is not None:
            data["taps_count"] = self.taps_count
        if self.duration_seconds is not None:
            data["duration_seconds"] = self.duration_seconds
        if self.tap_timestamps is not None:
            data["tap_timestamps"] = self.tap_timestamps
        if self.extra_data:
            data.update(self.extra_data)
        return data


class ProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    location_id: str
    is_new_unlock: bool
    artifact: ArtifactSchema
    unlocked_at: datetime
    message: str
    validation: Optional[MechanicValidationResult] = None
