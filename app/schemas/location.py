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


class TextsSchema(BaseModel):
    layer1: str
    layer2: str = ""


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
    success_threshold: float = Field(100.0, description="Threshold to win the mechanic and grab prize")


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order: int
    priority: Literal["P0", "P1", "P2"]
    title: str
    mechanic: Literal["trace", "tap_climb", "none"]
    mechanic_params: Dict[str, Any]
    marker: MarkerSchema
    model_url: str
    coordinates: CoordinatesSchema
    animations: List[AnimationSchema]
    texts: TextsSchema
    artifact: ArtifactSchema
