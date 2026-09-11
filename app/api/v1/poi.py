from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.db.models.poi import Poi
from app.schemas.poi import (
    PoiBatchReviewRequest,
    PoiRecommendationItem,
    PoiResponse,
    PoiReviewRequest,
    PoiSyncStatusResponse,
    PoiSyncTriggerRequest,
)
from app.services.poi.recommender import PoiRecommender
from app.services.poi.sync_manager import PoiSyncManager

router = APIRouter(prefix="/poi", tags=["POI & Quest Recommender"])


# ============================================================================
# Quest Editor Recommendations
# ============================================================================

@router.get(
    "/recommendations",
    response_model=List[PoiRecommendationItem],
    summary="Get intelligent POI recommendations for Quest Editor",
    description=(
        "Returns a ranked list of cultural, historical, and folklore POIs for route point creation. "
        "Supports spatial proximity (near_lat, near_lon), category filtering, tag overlap, "
        "and text search."
    ),
)
async def get_poi_recommendations(
    near_lat: Optional[float] = Query(None, description="Latitude of quest anchor or previous point"),
    near_lon: Optional[float] = Query(None, description="Longitude of quest anchor or previous point"),
    radius_meters: float = Query(2500.0, ge=100.0, le=50000.0, description="Search radius in meters"),
    category: Optional[str] = Query(None, description="Filter by primary category (monument, museum_culture, etc.)"),
    tags: Optional[str] = Query(None, description="Comma-separated tags (e.g. 'tatar_culture,ar_friendly')"),
    search: Optional[str] = Query(None, description="Text search by name or description"),
    status: str = Query("approved", description="Filter by moderation status: 'approved', 'pending', or 'all'"),
    exclude_ids: Optional[str] = Query(None, description="Comma-separated POI IDs to exclude"),
    limit: int = Query(10, ge=1, le=50, description="Max number of recommendations to return"),
    db: AsyncSession = Depends(get_db),
) -> List[PoiRecommendationItem]:
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    exclude_list = [e.strip() for e in exclude_ids.split(",")] if exclude_ids else None

    return await PoiRecommender.recommend(
        session=db,
        near_lat=near_lat,
        near_lon=near_lon,
        radius_meters=radius_meters,
        category=category,
        tags=tag_list,
        search=search,
        status=status,
        exclude_ids=exclude_list,
        limit=limit,
    )


# ============================================================================
# Admin Moderation & Human-in-the-Loop (HITL) Tag Review
# ============================================================================

@router.get(
    "/admin/pending",
    response_model=List[PoiResponse],
    summary="HITL: Get POIs pending admin tag review",
    description="Returns list of newly synchronized POIs that require admin verification.",
)
async def get_pending_pois(
    category: Optional[str] = Query(None, description="Filter by proposed category"),
    search: Optional[str] = Query(None, description="Search in name or description"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[PoiResponse]:
    query = select(Poi).where(Poi.status == "pending")

    if category:
        query = query.where(Poi.category == category)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Poi.name.ilike(search_pattern)) | (Poi.description.ilike(search_pattern))
        )

    query = query.order_by(Poi.created_at.desc()).offset(offset).limit(limit)
    res = await db.execute(query)
    pois = res.scalars().all()
    return [PoiResponse.model_validate(p) for p in pois]


@router.post(
    "/admin/{poi_id}/review",
    response_model=PoiResponse,
    summary="HITL: Confirm, modify tags, or reject a POI",
    description="Admin confirms proposed tags or specifies custom tags/category, setting status to 'approved' or 'rejected'.",
)
async def review_poi(
    poi_id: str,
    payload: PoiReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> PoiResponse:
    query = select(Poi).where(Poi.id == poi_id)
    res = await db.execute(query)
    poi = res.scalar_one_or_none()

    if not poi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"POI with ID '{poi_id}' not found",
        )

    poi.status = payload.status
    if payload.category:
        poi.category = payload.category
    if payload.tags is not None:
        poi.tags = payload.tags
    if payload.admin_notes is not None:
        poi.admin_notes = payload.admin_notes

    await db.commit()
    await db.refresh(poi)
    return PoiResponse.model_validate(poi)


@router.post(
    "/admin/batch-approve",
    summary="HITL: Batch approve multiple POIs",
    description="Bulk confirms multiple POIs with their proposed tags in a single operation.",
)
async def batch_approve_pois(
    payload: PoiBatchReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    query = select(Poi).where(Poi.id.in_(payload.poi_ids))
    res = await db.execute(query)
    pois = res.scalars().all()

    for p in pois:
        p.status = payload.status

    await db.commit()
    return {
        "status": "updated",
        "count": len(pois),
        "target_status": payload.status,
        "poi_ids": [p.id for p in pois],
    }


# ============================================================================
# Periodic / On-Demand Sync Endpoints
# ============================================================================

@router.post(
    "/sync/run",
    summary="Trigger POI synchronization from OpenStreetMap",
    description="Synchronizes Kazan POIs from OpenStreetMap Overpass API, performs auto-tagging, and tracks sync logs.",
)
async def run_sync(
    payload: PoiSyncTriggerRequest = PoiSyncTriggerRequest(),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    result = await PoiSyncManager.sync_pois(
        session=db,
        area_name=payload.area_name,
        force_remote=payload.force_remote,
        dry_run=payload.dry_run,
    )
    return result


@router.get(
    "/sync/status",
    response_model=PoiSyncStatusResponse,
    summary="Get POI synchronization and database statistics",
    description="Returns timestamp of last sync, counts of pending vs approved POIs, category breakdown, and recent sync logs.",
)
async def get_sync_status(
    db: AsyncSession = Depends(get_db),
) -> PoiSyncStatusResponse:
    status_data = await PoiSyncManager.get_sync_status(db)
    return PoiSyncStatusResponse(**status_data)


# ============================================================================
# Direct POI Details
# ============================================================================

@router.get(
    "/{poi_id}",
    response_model=PoiResponse,
    summary="Get details of a single POI",
)
async def get_poi_by_id(
    poi_id: str,
    db: AsyncSession = Depends(get_db),
) -> PoiResponse:
    query = select(Poi).where(Poi.id == poi_id)
    res = await db.execute(query)
    poi = res.scalar_one_or_none()

    if not poi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"POI with ID '{poi_id}' not found",
        )

    return PoiResponse.model_validate(poi)
