from collections import Counter
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.db.models.poi import Poi
from app.services.location_service import LocationService
from app.services.poi.sync_manager import PoiSyncManager

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(prefix="/admin", tags=["Admin Panel & Quest Editor"])


@router.get("", response_class=HTMLResponse, summary="Admin Dashboard")
@router.get("/", response_class=HTMLResponse, summary="Admin Dashboard (slash)")
async def admin_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    loc_service = LocationService(db)
    locations = await loc_service.get_all_locations()

    p0_count = sum(1 for loc in locations if loc.priority == "P0")
    p1_count = sum(1 for loc in locations if loc.priority == "P1")
    p2_count = sum(1 for loc in locations if loc.priority == "P2")
    mechanics_count = Counter(loc.mechanic for loc in locations)

    sync_status = await PoiSyncManager.get_sync_status(db)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "locations": locations,
            "total_locations": len(locations),
            "p0_count": p0_count,
            "p1_count": p1_count,
            "p2_count": p2_count,
            "mechanics_count": dict(mechanics_count),
            "total_pois": sync_status.get("total_pois", 0),
            "approved_pois_count": sync_status.get("approved_count", 0),
            "pending_pois_count": sync_status.get("pending_count", 0),
            "s3_ok": settings.is_s3_configured,
            "gpt_ok": settings.is_gpt_configured,
            "active_tab": "dashboard",
        },
    )


@router.get("/quests", response_class=HTMLResponse, summary="Quests List View")
async def quests_list(request: Request, db: AsyncSession = Depends(get_db)):
    loc_service = LocationService(db)
    locations = await loc_service.get_all_locations()

    return templates.TemplateResponse(
        request=request,
        name="quests/list.html",
        context={
            "locations": locations,
            "active_tab": "quests",
        },
    )


@router.get("/quests/new", response_class=HTMLResponse, summary="Create Quest View")
async def quest_create_view(request: Request, db: AsyncSession = Depends(get_db)):
    loc_service = LocationService(db)
    locations = await loc_service.get_all_locations()
    max_order = max((loc.order for loc in locations), default=0)

    return templates.TemplateResponse(
        request=request,
        name="quests/create.html",
        context={
            "all_locations": locations,
            "next_order": max_order + 1,
            "active_tab": "quests",
        },
    )


@router.get("/quests/{id}/edit", response_class=HTMLResponse, summary="Edit Quest View")
async def quest_edit_view(id: str, request: Request, db: AsyncSession = Depends(get_db)):
    loc_service = LocationService(db)
    locations = await loc_service.get_all_locations()

    location = next((loc for loc in locations if loc.id == id), None)
    if not location:
        raise HTTPException(status_code=404, detail=f"Location '{id}' not found")

    return templates.TemplateResponse(
        request=request,
        name="quests/edit.html",
        context={
            "location": location,
            "all_locations": locations,
            "active_tab": "quests",
        },
    )


@router.get("/pois", response_class=HTMLResponse, summary="POI Moderation View")
async def poi_moderation_view(
    request: Request,
    status: str = Query("pending"),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Poi)
    if status in ("pending", "approved", "rejected"):
        query = query.where(Poi.status == status)

    if search:
        pattern = f"%{search}%"
        query = query.where((Poi.name.ilike(pattern)) | (Poi.description.ilike(pattern)))

    query = query.order_by(Poi.created_at.desc()).limit(100)
    res = await db.execute(query)
    pois = res.scalars().all()

    # Counts
    pending_res = await db.execute(select(func.count(Poi.id)).where(Poi.status == "pending"))
    pending_count = pending_res.scalar() or 0

    approved_res = await db.execute(select(func.count(Poi.id)).where(Poi.status == "approved"))
    approved_count = approved_res.scalar() or 0

    return templates.TemplateResponse(
        request=request,
        name="poi/list.html",
        context={
            "pois": pois,
            "current_status": status,
            "pending_count": pending_count,
            "approved_count": approved_count,
            "search_query": search or "",
            "active_tab": "pois",
        },
    )


@router.get("/sync", response_class=HTMLResponse, summary="OSM Sync View")
async def poi_sync_view(request: Request, db: AsyncSession = Depends(get_db)):
    sync_status = await PoiSyncManager.get_sync_status(db)

    return templates.TemplateResponse(
        request=request,
        name="poi/sync.html",
        context={
            "sync_status": sync_status,
            "active_tab": "sync",
        },
    )
