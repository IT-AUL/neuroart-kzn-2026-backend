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
