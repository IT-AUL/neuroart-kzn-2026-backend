from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


POI_CATEGORIES = Literal[
    "monument",
    "museum_culture",
    "historic_quarter",
    "nature_view",
    "folklore_legends",
    "architecture_heritage",
    "other",
]

POI_STATUSES = Literal["pending", "approved", "rejected"]


class PoiResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    osm_id: str
    osm_type: str
    name: str
    name_en: Optional[str] = None
    name_tt: Optional[str] = None
    latitude: float
    longitude: float
    category: str
    tags: List[str] = Field(default_factory=list)
    proposed_category: Optional[str] = None
    proposed_tags: List[str] = Field(default_factory=list)
    raw_osm_tags: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
    status: str
    confidence_score: float
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_synced_at: datetime


class PoiRecommendationItem(BaseModel):
    poi: PoiResponse
    distance_meters: Optional[float] = None
    match_score: float = Field(..., description="Overall relevance score from 0.0 to 1.0+")
    reasons: List[str] = Field(default_factory=list, description="Explanatory badges for why this POI was recommended")


class PoiReviewRequest(BaseModel):
    status: Literal["approved", "rejected"] = "approved"
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    admin_notes: Optional[str] = None


class PoiBatchReviewRequest(BaseModel):
    poi_ids: List[str] = Field(..., min_length=1)
    status: Literal["approved", "rejected"] = "approved"


class PoiSyncTriggerRequest(BaseModel):
    area_name: str = Field("Kazan", description="Target city or area name")
    force_remote: bool = Field(False, description="If true, attempts live Overpass query; otherwise uses cached/fallback when remote is unavailable")
    dry_run: bool = Field(False, description="If true, parses points without committing to database")


class PoiSyncStatusResponse(BaseModel):
    last_synced_at: Optional[datetime] = None
    total_pois: int
    pending_count: int
    approved_count: int
    rejected_count: int
    categories_breakdown: Dict[str, int]
    recent_logs: List[Dict[str, Any]] = Field(default_factory=list)


class CreateLocationFromPoiRequest(BaseModel):
    poi_id: str = Field(..., description="ID of the POI to convert into a quest Location")
    order: int = Field(..., ge=1, description="Sequential route order index")
    priority: Literal["P0", "P1", "P2"] = "P1"
    mechanic: Literal["trace", "tap_climb", "none", "tap_strike", "strike"] = "none"
    custom_title: Optional[str] = Field(None, description="Optional custom override for location title")
