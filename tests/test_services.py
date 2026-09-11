import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "s3_configured" in data
    assert "yandex_gpt_configured" in data


@pytest.mark.asyncio
async def test_storage_status_endpoint(client: AsyncClient):
    response = await client.get("/storage/status")
    assert response.status_code == 200
    data = response.json()
    assert "configured" in data
    assert "bucket" in data
    assert "endpoint" in data


@pytest.mark.asyncio
async def test_storage_upload_endpoint(client: AsyncClient):
    file_content = b"fake 3d glb content"
    files = {"file": ("test_model.glb", file_content, "model/gltf-binary")}
    data = {"key_prefix": "models"}

    response = await client.post("/storage/upload", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["key"] == "models/test_model.glb"
    assert res_data["size_bytes"] == len(file_content)
    assert "url" in res_data


@pytest.mark.asyncio
async def test_ai_folklore_chat(client: AsyncClient):
    payload = {
        "prompt": "Расскажи, кто такой Шурале и почему дровосек перехитрил его?",
    }
    response = await client.post("/locations/loc_1_shurale/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["location_id"] == "loc_1_shurale"
    assert "Дровосек-батыр и Шурале" in data["location_title"]
    assert len(data["answer"]) > 0
    assert "model" in data


@pytest.mark.asyncio
async def test_api_v1_prefixed_routes(client: AsyncClient):
    # Verify routes are also accessible with /api/v1 prefix
    response = await client.get("/api/v1/locations")
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert data["locations_endpoint"] == "/locations"


@pytest.mark.asyncio
async def test_storage_presign_download_and_delete(client: AsyncClient):
    # Test presigned download URL generation
    presign_res = await client.get("/storage/presign/models/test_scene.glb")
    assert presign_res.status_code == 200
    presign_data = presign_res.json()
    assert presign_data["key"] == "models/test_scene.glb"
    assert "download_url" in presign_data
    assert presign_data["expires_in_seconds"] == 3600

    # Test deleting object
    del_res = await client.delete("/storage/object/models/test_scene.glb")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "deleted"
    assert del_data["key"] == "models/test_scene.glb"

