from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class MarkerSchema(BaseModel):
    type: str = "image"
    asset: str


class CoordinatesSchema(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    scale: float = 1.0


class AnimationSchema(BaseModel):
    id: int
    name: str


class ModelAssetSchema(BaseModel):
    id: str
    name: str
    url: str
    is_primary: bool = False


class DialogueReplicaSchema(BaseModel):
    speaker: str
    text: str
    trigger: Optional[str] = None


class TextsSchema(BaseModel):
    layer1: str
    layer2: str = ""
    action_hint: Optional[str] = None
    dialogue: Optional[List[DialogueReplicaSchema]] = None
    easter_egg: Optional[str] = None


class ArtifactSchema(BaseModel):
    id: str
    name: str
    icon: str


class NormalizedPoint(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0, description="Normalized X coordinate (0.0 to 1.0) of model frame")
    y: float = Field(..., ge=0.0, le=1.0, description="Normalized Y coordinate (0.0 to 1.0) of model frame")


class TraceParamsSchema(BaseModel):
    path: Union[str, List[NormalizedPoint]] = Field(
        ...,
        description="Contour path for tracing: array of normalized {x, y} points (0-1) or artist placeholder string",
    )
    tolerance: float = Field(
        20.0,
        description="Allowed finger deviation from line in pixels",
    )


class TapClimbParamsSchema(BaseModel):
    gain_per_tap: float = Field(4.0, description="Progress gained per tap")
    decay_per_interval: float = Field(1.0, description="Progress decay per tick")
    decay_interval_seconds: float = Field(0.3, description="Interval in seconds for decay tick")
    grace_period_seconds: float = Field(1.0, description="Pause buffer before decay begins")
    success_threshold: float = Field(100.0, description="Threshold to win the mechanic and grab prize")


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order: int
    priority: Literal["P0", "P1", "P2"]
    title: str
    mechanic: Literal["trace", "tap_climb", "none", "tap_strike", "strike"]
    mechanic_params: Dict[str, Any]
    marker: MarkerSchema
    model_url: str
    models: List[ModelAssetSchema] = Field(default_factory=list)
    coordinates: CoordinatesSchema
    animations: List[AnimationSchema]
    texts: TextsSchema
    artifact: ArtifactSchema
    next_location_id: Optional[str] = None
    next_location_order: Optional[int] = None
    next_location_hint: Optional[str] = None


class LocationCreateRequest(BaseModel):
    id: str = Field(..., min_length=2, max_length=64, description="Unique slug ID, e.g. 'loc_4_kaban'")
    order: int = Field(..., ge=1, description="Sequential route order")
    priority: Literal["P0", "P1", "P2"] = "P1"
    title: str = Field(..., min_length=2, max_length=255)
    mechanic: Literal["trace", "tap_climb", "none", "tap_strike", "strike"] = "none"
    mechanic_params: Dict[str, Any] = Field(default_factory=dict)
    marker: MarkerSchema = Field(default_factory=lambda: MarkerSchema(type="image", asset="marker_default.png"))
    model_url: Optional[str] = Field(default="", description="Primary 3D GLB model path or URL")
    models: List[ModelAssetSchema] = Field(default_factory=list, description="Sub-models in AR scene")
    coordinates: CoordinatesSchema = Field(default_factory=CoordinatesSchema)
    animations: List[AnimationSchema] = Field(default_factory=list)
    texts: TextsSchema
    artifact: ArtifactSchema
    next_location_id: Optional[str] = None
    next_location_order: Optional[int] = None
    next_location_hint: Optional[str] = None


class LocationUpdateRequest(BaseModel):
    order: Optional[int] = None
    priority: Optional[Literal["P0", "P1", "P2"]] = None
    title: Optional[str] = None
    mechanic: Optional[Literal["trace", "tap_climb", "none", "tap_strike", "strike"]] = None
    mechanic_params: Optional[Dict[str, Any]] = None
    marker: Optional[MarkerSchema] = None
    model_url: Optional[str] = None
    models: Optional[List[ModelAssetSchema]] = None
    coordinates: Optional[CoordinatesSchema] = None
    animations: Optional[List[AnimationSchema]] = None
    texts: Optional[TextsSchema] = None
    artifact: Optional[ArtifactSchema] = None
    next_location_id: Optional[str] = None
    next_location_order: Optional[int] = None
    next_location_hint: Optional[str] = None


