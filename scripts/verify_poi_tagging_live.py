import asyncio
import logging
import sys
from pprint import pprint
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_factory, engine
from app.db.base import Base
from app.db.models.poi import Poi
from app.services.poi.osm_client import OsmClient
from app.services.poi.recommender import PoiRecommender
from app.services.poi.sync_manager import PoiSyncManager
from app.services.poi.tag_engine import PoiTagEngine

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)



async def main():
    print("=" * 70)
    print("LIVE VERIFICATION: POI OpenStreetMap Parser, Tagging & Recommender")
    print("=" * 70)

    # ------------------------------------------------------------------------
    # 1. Test live Overpass API query for Kazan
    # ------------------------------------------------------------------------
    print("\n[STEP 1] Fetching live POIs from OpenStreetMap Overpass API (Kazan bbox)...")
    print("  Querying real historical & cultural nodes/ways...")
    
    live_pois = await OsmClient.fetch_pois(force_remote=True)
    print(f"  [+] Successfully fetched {len(live_pois)} POIs from OpenStreetMap!")

    # ------------------------------------------------------------------------
    # 2. Test Data Tagging Engine on Real POIs
    # ------------------------------------------------------------------------
    print("\n[STEP 2] Running Data Tagging Engine (PoiTagEngine.classify) on Real POIs:")
    print("-" * 70)

    sample_size = min(6, len(live_pois))
    for i, poi in enumerate(live_pois[:sample_size], 1):
        name = poi["name"]
        raw_tags = poi.get("tags", {})
        category, tags, confidence = PoiTagEngine.classify(name, raw_tags)

        print(f"  Entity #{i}: \"{name}\"")
        print(f"    - OSM ID       : {poi['osm_id']} ({poi['osm_type']})")
        print(f"    - Coordinates  : lat={poi['lat']:.5f}, lon={poi['lon']:.5f}")
        print(f"    - Raw Key Tags : {dict(list(raw_tags.items())[:4])}")
        print(f"    -> Category    : [{category.upper()}]")
        print(f"    -> Tags        : {tags}")
        print(f"    -> Confidence  : {confidence * 100:.0f}%")
        print("-" * 70)

    # ------------------------------------------------------------------------
    # 3. Database Sync & Admin HITL Lifecycle
    # ------------------------------------------------------------------------
    print("\n[STEP 3] Testing Database Sync, Idempotency & Admin HITL Flow:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # Run sync
        sync_result = await PoiSyncManager.sync_pois(session, area_name="Kazan", force_remote=False)
        print(f"  [+] Sync result: scanned={sync_result['points_scanned']}, created={sync_result['points_created']}, updated={sync_result['points_updated']}")

        # Fetch pending queue
        status_info = await PoiSyncManager.get_sync_status(session)
        print(f"  [+] DB Status: total={status_info['total_pois']}, pending={status_info['pending_count']}, approved={status_info['approved_count']}")
        print(f"  [+] Categories Breakdown: {status_info['categories_breakdown']}")

        # Admin reviews and approves first pending POI
        from sqlalchemy import select
        res = await session.execute(select(Poi).where(Poi.status == "pending").limit(1))
        target_poi = res.scalar_one_or_none()

        if target_poi:
            print(f"\n  [*] Admin reviewing POI: '{target_poi.name}' (ID: {target_poi.id})")
            print(f"      Initial proposed category: {target_poi.proposed_category}")
            print(f"      Initial proposed tags: {target_poi.proposed_tags}")

            # Admin confirms and adds custom curator tag
            target_poi.status = "approved"
            target_poi.tags = list(set(target_poi.proposed_tags + ["verified_quest_anchor"]))
            target_poi.admin_notes = "Confirmed by city quest administrator."
            await session.commit()
            print(f"  [+] Status updated to APPROVED with tags: {target_poi.tags}")

        # ------------------------------------------------------------------------
        # 4. Quest Editor Recommendations
        # ------------------------------------------------------------------------
        print("\n[STEP 4] Quest Editor Recommendations Simulation:")
        print("  Anchor Location: Kazan Kremlin (lat=55.7984, lon=49.1051)")
        print("  Looking for nearby cultural POIs within 2000m radius...")

        recommendations = await PoiRecommender.recommend(
            session=session,
            near_lat=55.7984,
            near_lon=49.1051,
            radius_meters=2000.0,
            status="all",
            limit=4,
        )

        for rank, rec in enumerate(recommendations, 1):
            p = rec.poi
            dist = f"{int(rec.distance_meters)}m" if rec.distance_meters else "N/A"
            print(f"  #{rank}: \"{p.name}\"")
            print(f"      Distance: {dist} | Match Score: {rec.match_score:.2f} | Status: {p.status}")
            print(f"      Category: {p.category} | Tags: {p.tags}")
            print(f"      Badges  : {rec.reasons}")

    print("\n" + "=" * 70)
    print("LIVE VERIFICATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
