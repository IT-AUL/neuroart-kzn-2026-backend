from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    text: str = Field(..., description="Message text")


class AIChatRequest(BaseModel):
    prompt: str = Field(..., description="User question or statement about the location")
    history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Optional prior chat history for multi-turn conversation",
    )


class AIChatResponse(BaseModel):
    location_id: str
    location_title: str
    answer: str
    model: str
    is_mock: bool = False


class LocationContentVariant(BaseModel):
    variant_id: str
    layer1: str = Field(..., description="Everyday practical / historical observation")
    layer2: str = Field(..., description="Mythological, cultural or historical background")
    action_hint: str = Field(..., description="Action prompt for player in AR scene")
    dialogue: List[dict] = Field(default_factory=list, description="Character speech lines")
    easter_egg: str = Field(..., description="Folklore joke or hidden story")
    artifact_suggestion: dict = Field(default_factory=dict, description="Suggested artifact id, name, icon")


class GenerateLocationContentRequest(BaseModel):
    title: str = Field(..., description="Location title to generate lore and descriptions for")
    context_or_theme: Optional[str] = Field(
        default=None,
        description="Optional additional context, keywords or theme (e.g. 'водяная, озеро, татарские сказки')",
    )
    variant_count: int = Field(default=2, ge=1, le=3, description="Number of distinct variants to generate")


class GenerateLocationContentResponse(BaseModel):
    title: str
    options: List[LocationContentVariant]
    model: str
    is_mock: bool = False


class ApproveContentRequest(BaseModel):
    """Payload for approving and applying selected/edited LLM variant to a location."""
    variant_id: Optional[str] = Field(default=None, description="ID of selected variant")
    layer1: Optional[str] = None
    layer2: Optional[str] = None
    action_hint: Optional[str] = None
    dialogue: Optional[List[dict]] = None
    easter_egg: Optional[str] = None
    artifact_name: Optional[str] = None
    artifact_id: Optional[str] = None
    artifact_icon: Optional[str] = None

