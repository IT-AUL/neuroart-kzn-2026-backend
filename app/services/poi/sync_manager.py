from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.poi import Poi, PoiSyncLog
from app.services.poi.osm_client import OsmClient
from app.services.poi.tag_engine import PoiTagEngine

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PoiSyncManager:
    """
    Manages synchronization of POIs from OpenStreetMap into the database,
    maintaining idempotency and preserving admin-approved curation.
    """

    @classmethod
    async def sync_pois(
        cls,
        session: AsyncSession,
        area_name: str = "Kazan",
        force_remote: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        started_at = utcnow()
        sync_log = PoiSyncLog(
            started_at=started_at,
            status="running",
            area_name=area_name,
        )
        if not dry_run:
            session.add(sync_log)
            await session.flush()

        points_created = 0
        points_updated = 0
        points_scanned = 0

        try:
            raw_pois = await OsmClient.fetch_pois(force_remote=force_remote)
            points_scanned = len(raw_pois)

            for item in raw_pois:
                osm_id = item["osm_id"]
                name = item["name"]
                lat = item["lat"]
                lon = item["lon"]
                raw_tags = item.get("tags", {})
                desc = item.get("description")
                osm_type = item.get("osm_type", "node")

                proposed_category, proposed_tags, confidence = PoiTagEngine.classify(
                    name=name,
                    osm_tags=raw_tags,
                )

                # Query existing POI by osm_id
                query = select(Poi).where(Poi.osm_id == osm_id)
                res = await session.execute(query)
                existing_poi: Optional[Poi] = res.scalar_one_or_none()

                if existing_poi is None:
                    # New POI discovered
                    cleaned_id = f"poi_{osm_type}_{osm_id.replace('/', '_')}"
                    new_poi = Poi(
                        id=cleaned_id,
                        osm_id=osm_id,
                        osm_type=osm_type,
                        name=name,
                        name_en=item.get("name_en"),
                        name_tt=item.get("name_tt"),
                        latitude=lat,
                        longitude=lon,
                        category=proposed_category,
                        tags=proposed_tags,
                        proposed_category=proposed_category,
                        proposed_tags=proposed_tags,
                        raw_osm_tags=raw_tags,
                        description=desc,
                        status="pending",
                        confidence_score=confidence,
                        created_at=started_at,
                        updated_at=started_at,
                        last_synced_at=started_at,
                    )
                    if not dry_run:
                        session.add(new_poi)
                    points_created += 1
                else:
                    # Existing POI: update spatial data and refresh tags if not yet approved
                    if not dry_run:
                        existing_poi.latitude = lat
                        existing_poi.longitude = lon
                        existing_poi.raw_osm_tags = raw_tags
                        existing_poi.last_synced_at = started_at
                        if desc and not existing_poi.description:
                            existing_poi.description = desc

                        # If pending or rejected, update proposed tags
                        if existing_poi.status != "approved":
                            existing_poi.proposed_category = proposed_category
                            existing_poi.proposed_tags = proposed_tags
                            existing_poi.category = proposed_category
                            existing_poi.tags = proposed_tags
                            existing_poi.confidence_score = confidence
                        # Note: If status == "approved", admin manual curation is PRESERVED!

                    points_updated += 1

            if not dry_run:
                sync_log.status = "success"
                sync_log.completed_at = utcnow()
                sync_log.points_scanned = points_scanned
                sync_log.points_created = points_created
                sync_log.points_updated = points_updated
                await session.commit()

            return {
                "status": "success" if not dry_run else "dry_run",
                "area_name": area_name,
                "points_scanned": points_scanned,
                "points_created": points_created,
                "points_updated": points_updated,
                "sync_time": (utcnow() - started_at).total_seconds(),
            }

        except Exception as exc:
            logger.error("Error during POI synchronization: %s", exc)
            if not dry_run:
                sync_log.status = "failed"
                sync_log.completed_at = utcnow()
                sync_log.error_message = str(exc)
                await session.commit()
            raise exc

    @classmethod
    async def get_sync_status(cls, session: AsyncSession) -> Dict[str, Any]:
        # Count totals and by status
        total_stmt = select(func.count(Poi.id))
        total_pois = (await session.execute(total_stmt)).scalar() or 0

        pending_stmt = select(func.count(Poi.id)).where(Poi.status == "pending")
        pending_count = (await session.execute(pending_stmt)).scalar() or 0

        approved_stmt = select(func.count(Poi.id)).where(Poi.status == "approved")
        approved_count = (await session.execute(approved_stmt)).scalar() or 0

        rejected_stmt = select(func.count(Poi.id)).where(Poi.status == "rejected")
        rejected_count = (await session.execute(rejected_stmt)).scalar() or 0

        # Categories breakdown
        cat_stmt = select(Poi.category, func.count(Poi.id)).group_by(Poi.category)
        cat_rows = (await session.execute(cat_stmt)).all()
        categories_breakdown = {row[0]: row[1] for row in cat_rows}

        # Last sync log
        log_stmt = select(PoiSyncLog).order_by(PoiSyncLog.started_at.desc()).limit(5)
        recent_logs_objs = (await session.execute(log_stmt)).scalars().all()
        recent_logs = [
            {
                "id": log.id,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                "status": log.status,
                "points_scanned": log.points_scanned,
                "points_created": log.points_created,
                "points_updated": log.points_updated,
                "area_name": log.area_name,
                "error_message": log.error_message,
            }
            for log in recent_logs_objs
        ]

        last_synced_at = recent_logs_objs[0].completed_at if recent_logs_objs and recent_logs_objs[0].completed_at else None

        return {
            "last_synced_at": last_synced_at,
            "total_pois": total_pois,
            "pending_count": pending_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "categories_breakdown": categories_breakdown,
            "recent_logs": recent_logs,
        }
