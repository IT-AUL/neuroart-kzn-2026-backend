from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.location import ArtifactSchema


class PassportArtifactItem(ArtifactSchema):
    location_id: str
    unlocked_at: datetime


class PassportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    total_slots: int = 10
    collected_count: int
    artifacts: List[PassportArtifactItem]
