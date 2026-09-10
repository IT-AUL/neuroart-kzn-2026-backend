from fastapi import APIRouter
from app.api.v1.ai import router as ai_router
from app.api.v1.locations import router as locations_router
from app.api.v1.passport import router as passport_router
from app.api.v1.progress import router as progress_router
from app.api.v1.storage import router as storage_router

api_v1_router = APIRouter()

api_v1_router.include_router(locations_router)
api_v1_router.include_router(progress_router)
api_v1_router.include_router(passport_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(storage_router)
