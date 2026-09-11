import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.admin.router import router as admin_router
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


def _sync_sqlite_migrate(sync_conn):
    """Ensure missing columns are added to existing SQLite tables without losing data."""
    try:
        res = sync_conn.exec_driver_sql("PRAGMA table_info(locations);")
        columns = {row[1] for row in res.fetchall()}
        if columns:
            if "models" not in columns:
                sync_conn.exec_driver_sql("ALTER TABLE locations ADD COLUMN models JSON NOT NULL DEFAULT '[]';")
                logger.info("Auto-migrated SQLite: added column locations.models")
            if "next_location_id" not in columns:
                sync_conn.exec_driver_sql("ALTER TABLE locations ADD COLUMN next_location_id VARCHAR(64) NULL;")
                logger.info("Auto-migrated SQLite: added column locations.next_location_id")
            if "next_location_order" not in columns:
                sync_conn.exec_driver_sql("ALTER TABLE locations ADD COLUMN next_location_order INTEGER NULL;")
                logger.info("Auto-migrated SQLite: added column locations.next_location_order")
            if "next_location_hint" not in columns:
                sync_conn.exec_driver_sql("ALTER TABLE locations ADD COLUMN next_location_hint VARCHAR(512) NULL;")
                logger.info("Auto-migrated SQLite: added column locations.next_location_hint")
    except Exception as exc:
        logger.error("Schema auto-migration error: %s", exc)
        raise exc



@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_sync_sqlite_migrate)

    logger.info("Running location seeds...")
    async with async_session_factory() as session:
        await seed_locations(session)

    logger.info("Checking POI dataset seeds...")
    async with async_session_factory() as session:
        from sqlalchemy import update
        from app.db.models.poi import Poi
        from app.services.poi.sync_manager import PoiSyncManager

        poi_status = await PoiSyncManager.get_sync_status(session)
        if poi_status["total_pois"] == 0:
            logger.info("Initializing baseline Kazan POIs...")
            await PoiSyncManager.sync_pois(session, area_name="Kazan")
            await session.execute(update(Poi).values(status="approved"))
            await session.commit()

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

# Static files for Admin Panel
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Admin Panel & Quest Editor (Jinja2 SSR)
app.include_router(admin_router)

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
        "admin_panel": "/admin",
        "locations_endpoint": "/locations",
        "passport_endpoint": "/passport",
    }
