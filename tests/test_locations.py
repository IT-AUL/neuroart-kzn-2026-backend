import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_all_locations(client: AsyncClient):
    response = await client.get("/locations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3

    # Verify ordering
    orders = [loc["order"] for loc in data]
    assert orders == [1, 2, 3]

    # Verify IDs
    ids = [loc["id"] for loc in data]
    assert ids == ["loc_1_shurale", "loc_2_sabantuy", "loc_3_chak_chak"]


@pytest.mark.asyncio
async def test_get_shurale_location(client: AsyncClient):
    response = await client.get("/locations/loc_1_shurale")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "loc_1_shurale"
    assert data["order"] == 1
    assert data["priority"] == "P0"
    assert data["title"] == "Дровосек-батыр и Шурале"
    assert data["mechanic"] == "trace"
    assert data["mechanic_params"]["tolerance"] == 20
    assert "заполняет 3D-художник" in data["mechanic_params"]["path"]
    assert data["marker"] == {"type": "image", "asset": "marker_log.png"}
    assert data["model_url"].endswith("models/loc1_log_shurale.glb")
    assert data["coordinates"] == {"x": 0.0, "y": 0.0, "z": 0.0, "scale": 1.0}
    assert len(data["animations"]) == 8
    assert data["animations"][0] == {"id": 0, "name": "log_idle_crack_closed"}
    assert "Тукая" in data["texts"]["layer2"]
    assert data["artifact"] == {"id": "klin", "name": "Клин", "icon": "icons/klin.png"}


@pytest.mark.asyncio
async def test_get_sabantuy_location(client: AsyncClient):
    response = await client.get("/locations/loc_2_sabantuy")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "loc_2_sabantuy"
    assert data["order"] == 2
    assert data["priority"] == "P1"
    assert data["title"] == "Сабантуй, лазание на столб"
    assert data["mechanic"] == "tap_climb"
    params = data["mechanic_params"]
    assert params["gain_per_tap"] == 4
    assert params["decay_per_interval"] == 1
    assert params["decay_interval_seconds"] == 0.3
    assert params["success_threshold"] == 100
    assert data["artifact"]["id"] == "polotentse"


@pytest.mark.asyncio
async def test_get_chak_chak_location(client: AsyncClient):
    response = await client.get("/locations/loc_3_chak_chak")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "loc_3_chak_chak"
    assert data["order"] == 3
    assert data["priority"] == "P2"
    assert data["mechanic"] == "none"
    assert data["mechanic_params"] == {}
    assert data["artifact"]["id"] == "chak_chak"


@pytest.mark.asyncio
async def test_get_location_not_found(client: AsyncClient):
    response = await client.get("/locations/unknown_loc_999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
