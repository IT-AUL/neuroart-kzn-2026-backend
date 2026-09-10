import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_progress_missing_session_header(client: AsyncClient):
    response = await client.post("/progress/loc_1_shurale")
    assert response.status_code == 400
    assert "X-Session-ID" in response.json()["detail"]


@pytest.mark.asyncio
async def test_progress_unknown_location(client: AsyncClient):
    session_id = str(uuid.uuid4())
    response = await client.post(
        "/progress/unknown_point",
        headers={"X-Session-ID": session_id},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_progress_unlock_and_passport(client: AsyncClient):
    session_id = str(uuid.uuid4())
    headers = {"X-Session-ID": session_id}

    # Initial passport state should be empty
    passport_resp = await client.get("/passport", headers=headers)
    assert passport_resp.status_code == 200
    passport_data = passport_resp.json()
    assert passport_data["session_id"] == session_id
    assert passport_data["total_slots"] == 10
    assert passport_data["collected_count"] == 0
    assert passport_data["artifacts"] == []

    # Complete location 1 (Shurale)
    prog_resp = await client.post("/progress/loc_1_shurale", headers=headers)
    assert prog_resp.status_code == 200
    prog_data = prog_resp.json()
    assert prog_data["is_new_unlock"] is True
    assert prog_data["artifact"]["id"] == "klin"
    assert prog_data["artifact"]["name"] == "Клин"

    # Passport state after 1 unlock
    passport_resp = await client.get("/passport", headers=headers)
    passport_data = passport_resp.json()
    assert passport_data["collected_count"] == 1
    assert len(passport_data["artifacts"]) == 1
    assert passport_data["artifacts"][0]["id"] == "klin"
    assert passport_data["artifacts"][0]["location_id"] == "loc_1_shurale"


@pytest.mark.asyncio
async def test_progress_idempotency(client: AsyncClient):
    session_id = str(uuid.uuid4())
    headers = {"X-Session-ID": session_id}

    # First call: unlocks artifact
    resp1 = await client.post("/progress/loc_2_sabantuy", headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["is_new_unlock"] is True

    # Second call (same location, same session): returns existing, does NOT duplicate
    resp2 = await client.post("/progress/loc_2_sabantuy", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["is_new_unlock"] is False
    assert resp2.json()["artifact"]["id"] == "polotentse"

    # Third call
    resp3 = await client.post("/progress/loc_2_sabantuy", headers=headers)
    assert resp3.status_code == 200
    assert resp3.json()["is_new_unlock"] is False

    # Check passport: strictly 1 item
    passport_resp = await client.get("/passport", headers=headers)
    passport_data = passport_resp.json()
    assert passport_data["collected_count"] == 1
    assert len(passport_data["artifacts"]) == 1


@pytest.mark.asyncio
async def test_session_isolation(client: AsyncClient):
    session_a = str(uuid.uuid4())
    session_b = str(uuid.uuid4())

    # Session A completes 2 locations
    await client.post("/progress/loc_1_shurale", headers={"X-Session-ID": session_a})
    await client.post("/progress/loc_3_chak_chak", headers={"X-Session-ID": session_a})

    # Session B completes 1 location
    await client.post("/progress/loc_2_sabantuy", headers={"X-Session-ID": session_b})

    # Check Passport A
    resp_a = await client.get("/passport", headers={"X-Session-ID": session_a})
    data_a = resp_a.json()
    assert data_a["collected_count"] == 2
    artifact_ids_a = {art["id"] for art in data_a["artifacts"]}
    assert artifact_ids_a == {"klin", "chak_chak"}

    # Check Passport B
    resp_b = await client.get("/passport", headers={"X-Session-ID": session_b})
    data_b = resp_b.json()
    assert data_b["collected_count"] == 1
    assert data_b["artifacts"][0]["id"] == "polotentse"
