import argparse
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.core.config import settings
from app.core.database import async_session_factory, engine
from app.db.base import Base
from app.services.poi.sync_manager import PoiSyncManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [poi-service]: %(message)s",
)
logger = logging.getLogger("poi-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting POI Microservice...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initial sync check
    async with async_session_factory() as session:
        status = await PoiSyncManager.get_sync_status(session)
        if status["total_pois"] == 0:
            logger.info("No POIs found in database. Running initial Kazan sync...")
            await PoiSyncManager.sync_pois(session, area_name="Kazan")

    yield
    logger.info("Shutting down POI Microservice...")
    await engine.dispose()


standalone_app = FastAPI(
    title="NeuroArt POI Parser & Recommender Microservice",
    version="1.0.0",
    description="Microservice for OpenStreetMap POI synchronization, categorization, and quest editor recommendations.",
    lifespan=lifespan,
)

standalone_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Deferred router import to avoid circular dependencies
from app.api.v1.poi import router as poi_router
standalone_app.include_router(poi_router, prefix="/api/v1")
standalone_app.include_router(poi_router)


@standalone_app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "service": "poi-parser-recommender"}


def main():
    parser = argparse.ArgumentParser(description="Run POI microservice standalone")
    parser.add_argument("--host", default="0.0.0.0", help="Binding host")
    parser.add_argument("--port", type=int, default=8001, help="Binding port")
    args = parser.parse_args()

    uvicorn.run("app.services.poi.standalone:standalone_app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
