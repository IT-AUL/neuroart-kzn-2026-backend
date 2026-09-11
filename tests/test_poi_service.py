import pytest
from httpx import AsyncClient
from app.services.poi.tag_engine import (
    CATEGORY_FOLKLORE_LEGENDS,
    CATEGORY_HISTORIC_QUARTER,
    CATEGORY_MONUMENT,
    CATEGORY_MUSEUM_CULTURE,
    TAG_TATAR_CULTURE,
    TAG_UNESCO,
    PoiTagEngine,
)


# ============================================================================
# 1. Unit Tests: Tag Engine & Classification
# ============================================================================

def test_tag_engine_monument_classification():
    category, tags, confidence = PoiTagEngine.classify(
        name="Памятник Мусе Джалилю",
        osm_tags={"historic": "monument", "artwork_type": "statue"},
    )
    assert category == CATEGORY_MONUMENT
    assert TAG_TATAR_CULTURE in tags
    assert confidence >= 0.90


def test_tag_engine_unesco_and_historic_quarter():
    category, tags, confidence = PoiTagEngine.classify(
        name="Казанский кремль",
        osm_tags={"historic": "heritage", "heritage": "UNESCO"},
    )
    assert category == CATEGORY_HISTORIC_QUARTER
    assert TAG_UNESCO in tags
    assert TAG_TATAR_CULTURE in tags


def test_tag_engine_folklore_detection():
    category, tags, confidence = PoiTagEngine.classify(
        name="Скульптура Дракона Зилант",
        osm_tags={"historic": "monument", "artwork_type": "sculpture"},
    )
    assert category == CATEGORY_FOLKLORE_LEGENDS
    assert "family_friendly" in tags
    assert TAG_TATAR_CULTURE in tags


def test_tag_engine_museum():
    category, tags, confidence = PoiTagEngine.classify(
        name="Музей исламской культуры",
        osm_tags={"tourism": "museum"},
    )
    assert category == CATEGORY_MUSEUM_CULTURE
    assert confidence >= 0.90


# ============================================================================
# 2. Integration Tests: POI Sync, Idempotency & Status
# ============================================================================

@pytest.mark.asyncio
async def test_poi_sync_and_idempotency(client: AsyncClient):
    # 1. Run initial sync
    sync_resp = await client.post("/poi/sync/run", json={"area_name": "Kazan", "dry_run": False})
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["status"] == "success"
    assert sync_data["points_created"] >= 10
    first_created = sync_data["points_created"]

    # 2. Check sync status
    status_resp = await client.get("/poi/sync/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["total_pois"] == first_created
    assert status_data["pending_count"] == first_created
    assert len(status_data["recent_logs"]) >= 1

    # 3. Rerun sync -> verify idempotency (0 created, all updated)
    resync_resp = await client.post("/poi/sync/run", json={"area_name": "Kazan", "dry_run": False})
    assert resync_resp.status_code == 200
    resync_data = resync_resp.json()
    assert resync_data["points_created"] == 0
    assert resync_data["points_updated"] == first_created


# ============================================================================
# 3. Integration Tests: Admin HITL Review Workflow
# ============================================================================

@pytest.mark.asyncio
async def test_admin_poi_review_and_curation_preservation(client: AsyncClient):
    # Seed points via sync
    await client.post("/poi/sync/run", json={"area_name": "Kazan", "dry_run": False})

    # Fetch pending points
    pending_resp = await client.get("/poi/admin/pending?limit=5")
    assert pending_resp.status_code == 200
    pending_list = pending_resp.json()
    assert len(pending_list) > 0
    target_poi = pending_list[0]
    target_id = target_poi["id"]

    # Review and approve target POI with custom tags
    review_payload = {
        "status": "approved",
        "category": "folklore_legends",
        "tags": ["custom_curated_tag", "tatar_culture"],
        "admin_notes": "Reviewed and verified by chief quest curator",
    }
    review_resp = await client.post(f"/poi/admin/{target_id}/review", json=review_payload)
    assert review_resp.status_code == 200
    reviewed_poi = review_resp.json()
    assert reviewed_poi["status"] == "approved"
    assert reviewed_poi["category"] == "folklore_legends"
    assert "custom_curated_tag" in reviewed_poi["tags"]
    assert reviewed_poi["admin_notes"] == "Reviewed and verified by chief quest curator"

    # Verify curation preservation during subsequent sync!
    await client.post("/poi/sync/run", json={"area_name": "Kazan", "dry_run": False})
    get_resp = await client.get(f"/poi/{target_id}")
    assert get_resp.status_code == 200
    after_sync_poi = get_resp.json()
    assert after_sync_poi["status"] == "approved"
    assert after_sync_poi["category"] == "folklore_legends"
    assert "custom_curated_tag" in after_sync_poi["tags"]


@pytest.mark.asyncio
async def test_admin_batch_approve(client: AsyncClient):
    await client.post("/poi/sync/run", json={"area_name": "Kazan", "dry_run": False})
    pending_resp = await client.get("/poi/admin/pending?limit=3")
    pending_ids = [p["id"] for p in pending_resp.json()]

    batch_resp = await client.post(
        "/poi/admin/batch-approve",
        json={"poi_ids": pending_ids, "status": "approved"},
    )
    assert batch_resp.status_code == 200
    assert batch_resp.json()["count"] == len(pending_ids)


# ============================================================================
# 4. Integration Tests: Recommendations for Quest Editor
# ============================================================================

@pytest.mark.asyncio
async def test_poi_recommendations_spatial_and_filters(client: AsyncClient):
    await client.post("/poi/sync/run", json={"area_name": "Kazan", "dry_run": False})

    # Approve all so they appear in default recommendations
    pending_resp = await client.get("/poi/admin/pending?limit=50")
    pending_ids = [p["id"] for p in pending_resp.json()]
    await client.post("/poi/admin/batch-approve", json={"poi_ids": pending_ids, "status": "approved"})

    # 1. Recommend near Kazan Kremlin (55.7984, 49.1051)
    rec_resp = await client.get("/poi/recommendations?near_lat=55.7984&near_lon=49.1051&radius_meters=1000")
    assert rec_resp.status_code == 200
    items = rec_resp.json()
    assert len(items) >= 1
    # Top item should be very close to the center
    top_item = items[0]
    assert top_item["distance_meters"] is not None
    assert top_item["distance_meters"] <= 500.0
    assert top_item["match_score"] > 0.4
    assert len(top_item["reasons"]) > 0

    # 2. Filter by category
    cat_resp = await client.get("/poi/recommendations?category=monument&status=all")
    assert cat_resp.status_code == 200
    cat_items = cat_resp.json()
    assert all(item["poi"]["category"] == "monument" for item in cat_items)

    # 3. Search query
    search_resp = await client.get("/poi/recommendations?search=Кот&status=all")
    assert search_resp.status_code == 200
    search_items = search_resp.json()
    assert len(search_items) >= 1
    assert "Кот" in search_items[0]["poi"]["name"]


# ============================================================================
# 5. Integration Tests: Convert Recommended POI to Route Location
# ============================================================================

@pytest.mark.asyncio
async def test_convert_poi_to_route_location(client: AsyncClient):
    await client.post("/poi/sync/run", json={"area_name": "Kazan", "dry_run": False})

    # Get a POI
    pending = await client.get("/poi/admin/pending?limit=1")
    poi = pending.json()[0]

    # Convert to Location
    payload = {
        "poi_id": poi["id"],
        "order": 4,
        "priority": "P1",
        "mechanic": "trace",
        "custom_title": "AR Квест: Кот Казанский",
    }
    create_resp = await client.post("/locations/from-poi", json=payload)
    assert create_resp.status_code == 201
    loc = create_resp.json()
    assert loc["order"] == 4
    assert loc["priority"] == "P1"
    assert loc["title"] == "AR Квест: Кот Казанский"
    assert loc["mechanic"] == "trace"
    assert "marker" in loc
    assert "texts" in loc
    assert "artifact" in loc

    # Verify it now appears in standard GET /locations
    all_locs = await client.get("/locations")
    assert any(l["id"] == loc["id"] for l in all_locs.json())


# ============================================================================
# 6. Negative Tests & Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_poi_get_by_id_and_not_found(client: AsyncClient):
    await client.post("/poi/sync/run", json={"area_name": "Kazan", "dry_run": False})
    pending = await client.get("/poi/admin/pending?limit=1")
    poi_id = pending.json()[0]["id"]

    # Valid ID -> 200
    res = await client.get(f"/poi/{poi_id}")
    assert res.status_code == 200
    assert res.json()["id"] == poi_id

    # Non-existent ID -> 404
    bad_res = await client.get("/poi/nonexistent_poi_id")
    assert bad_res.status_code == 404


@pytest.mark.asyncio
async def test_poi_admin_review_not_found(client: AsyncClient):
    res = await client.post(
        "/poi/admin/nonexistent_poi_id/review",
        json={"status": "approved", "admin_notes": "test"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_convert_poi_to_location_not_found(client: AsyncClient):
    res = await client.post(
        "/locations/from-poi",
        json={"poi_id": "nonexistent_poi_id", "order": 5},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_poi_sync_dry_run(client: AsyncClient):
    # Dry run should return counts without saving to DB
    sync_resp = await client.post("/poi/sync/run", json={"area_name": "Kazan", "dry_run": True})
    assert sync_resp.status_code == 200
    data = sync_resp.json()
    assert data["status"] == "dry_run"
    assert data["points_created"] >= 10

    # Status check should report 0 POIs in DB
    status_resp = await client.get("/poi/sync/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["total_pois"] == 0


@pytest.mark.asyncio
async def test_poi_recommendations_exclude_and_radius(client: AsyncClient):
    await client.post("/poi/sync/run", json={"area_name": "Kazan", "dry_run": False})
    pending = await client.get("/poi/admin/pending?limit=50")
    ids = [p["id"] for p in pending.json()]
    await client.post("/poi/admin/batch-approve", json={"poi_ids": ids, "status": "approved"})

    # Test exclusion
    first_id = ids[0]
    rec_resp = await client.get(f"/poi/recommendations?exclude_ids={first_id}&status=all")
    assert rec_resp.status_code == 200
    returned_ids = [item["poi"]["id"] for item in rec_resp.json()]
    assert first_id not in returned_ids

    # Test small radius at distant coordinates excludes all points
    # (Coordinates far away from Kazan, radius 100 meters satisfying ge=100)
    narrow_resp = await client.get("/poi/recommendations?near_lat=10.0000&near_lon=10.0000&radius_meters=100")
    assert narrow_resp.status_code == 200
    assert len(narrow_resp.json()) == 0



@pytest.mark.asyncio
async def test_poi_admin_pending_pagination_and_filters(client: AsyncClient):
    await client.post("/poi/sync/run", json={"area_name": "Kazan", "dry_run": False})

    # Page 1 (limit 2, offset 0)
    page1 = await client.get("/poi/admin/pending?limit=2&offset=0")
    assert page1.status_code == 200
    items1 = page1.json()
    assert len(items1) == 2

    # Page 2 (limit 2, offset 2)
    page2 = await client.get("/poi/admin/pending?limit=2&offset=2")
    assert page2.status_code == 200
    items2 = page2.json()
    assert len(items2) == 2

    # Verify no ID overlap between pages
    page1_ids = {p["id"] for p in items1}
    page2_ids = {p["id"] for p in items2}
    assert page1_ids.isdisjoint(page2_ids)

