import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_storage_presign_upload(client: AsyncClient):
    payload = {
        "filename": "loc4_lake_model.glb",
        "content_type": "model/gltf-binary",
        "key_prefix": "models",
    }
    response = await client.post("/storage/presign-upload", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "upload_url" in data
    assert "public_url" in data
    assert data["key"] == "models/loc4_lake_model.glb"
    assert data["method"] == "PUT"
    assert data["content_type"] == "model/gltf-binary"


@pytest.mark.asyncio
async def test_editor_generate_content(client: AsyncClient):
    payload = {
        "title": "Зилант — дракон Казани",
        "context_or_theme": "древняя крепость, крылатый змей, герб Казани",
        "variant_count": 2,
    }
    response = await client.post("/locations/editor/generate-content", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Зилант — дракон Казани"
    assert len(data["options"]) == 2

    # Verify first option structure
    opt = data["options"][0]
    assert "variant_id" in opt
    assert "layer1" in opt
    assert "layer2" in opt
    assert "action_hint" in opt
    assert len(opt["dialogue"]) >= 1
    assert "easter_egg" in opt
    assert "artifact_suggestion" in opt


@pytest.mark.asyncio
async def test_editor_approve_content(client: AsyncClient):
    # Approve custom content for location 2 (filling in previous placeholders)
    payload = {
        "variant_id": "variant_custom",
        "layer2": "На Сабантуе также состязаются в беге в мешках и перетягивании каната.",
        "action_hint": "Тапайте часто, чтобы забраться на столб за полотенцем!",
        "easter_egg": "Шутка Сабантуя: кто первый залез на столб, тот баран не покупает, а на руках несёт!",
    }
    response = await client.post("/locations/loc_2_sabantuy/editor/approve-content", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["texts"]["layer2"] == "На Сабантуе также состязаются в беге в мешках и перетягивании каната."
    assert "Шутка Сабантуя" in data["texts"]["easter_egg"]
    assert "Тапайте часто" in data["texts"]["action_hint"]
