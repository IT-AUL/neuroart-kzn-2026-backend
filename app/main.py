import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import async_session_factory, engine
from app.db.base import Base
from app.db.seeds.seeder import seed_locations

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("neuroart")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Running location seeds...")
    async with async_session_factory() as session:
        await seed_locations(session)

    logger.info("Application startup complete.")
    yield
    logger.info("Shutting down application...")
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "Backend API for NeuroArt KZN 2026 interactive route.\n\n"
        "- **Route Points (Locations)** with 3D model URLs, animations, texts, and mechanics (trace, tap_climb, none)\n"
        "- **Session Passport System** with idempotent progress tracking (10 demo slots)\n"
        "- **Yandex Cloud Object Storage (S3)** for 3D assets, markers, and icons\n"
        "- **Yandex LLM (YandexGPT)** for folklore guides and character interactions"
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level endpoints matching prompt specifications directly:
# /locations, /locations/{id}, /progress/{location_id}, /passport
app.include_router(api_v1_router)

# Also expose under /api/v1 prefix
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "s3_configured": settings.is_s3_configured,
        "yandex_gpt_configured": settings.is_gpt_configured,
    }


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Welcome to NeuroArt KZN 2026 Backend API",
        "docs": "/docs",
        "locations_endpoint": "/locations",
        "passport_endpoint": "/passport",
    }
