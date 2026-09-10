from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.location_service import LocationService
from app.services.yandex_llm_service import yandex_llm_service

router = APIRouter(prefix="/locations", tags=["AI Folklore Guide (YandexGPT)"])


@router.post(
    "/{id}/chat",
    response_model=AIChatResponse,
    summary="Chat with YandexGPT about location history, folklore, and secrets",
    description=(
        "Sends a question to the YandexGPT foundation model, personalized with the folklore "
        "and cultural context of this route point (layer1 & layer2 texts)."
    ),
)
async def chat_with_location_guide(
    id: str,
    payload: AIChatRequest,
    db: AsyncSession = Depends(get_db),
) -> AIChatResponse:
    loc_service = LocationService(db)
    location = await loc_service.get_location_by_id(location_id=id)

    return await yandex_llm_service.chat_about_location(
        location=location,
        user_prompt=payload.prompt,
        history=payload.history,
    )
