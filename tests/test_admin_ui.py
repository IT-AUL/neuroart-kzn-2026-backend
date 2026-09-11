import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_dashboard(client: AsyncClient):
    res = await client.get("/admin")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "NeuroArt KZN" in res.text
    assert "Панель управления" in res.text
    assert "Точек маршрута" in res.text


@pytest.mark.asyncio
async def test_admin_quests_list(client: AsyncClient):
    res = await client.get("/admin/quests")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "Точки маршрута и квесты" in res.text
    assert "loc_1_shurale" in res.text


@pytest.mark.asyncio
async def test_admin_quest_create_view(client: AsyncClient):
    res = await client.get("/admin/quests/new")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "Создание новой точки маршрута" in res.text
    assert "loc-id" in res.text


@pytest.mark.asyncio
async def test_admin_quest_edit_view(client: AsyncClient):
    res = await client.get("/admin/quests/loc_1_shurale/edit")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "loc_1_shurale" in res.text
    assert "Шурале" in res.text
    assert "trace" in res.text
    assert "AI-Ассистент контента" in res.text


@pytest.mark.asyncio
async def test_admin_quest_edit_not_found(client: AsyncClient):
    res = await client.get("/admin/quests/non_existent_loc/edit")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_admin_poi_views(client: AsyncClient):
    # Pending view
    res = await client.get("/admin/pois?status=pending")
    assert res.status_code == 200
    assert "Модерация объектов (POI)" in res.text

    # Approved view
    res = await client.get("/admin/pois?status=approved")
    assert res.status_code == 200
    assert "Одобренные POI" in res.text


@pytest.mark.asyncio
async def test_admin_sync_view(client: AsyncClient):
    res = await client.get("/admin/sync")
    assert res.status_code == 200
    assert "Синхронизация с OpenStreetMap" in res.text
    assert "Всего POI в базе" in res.text


@pytest.mark.asyncio
async def test_static_assets(client: AsyncClient):
    css_res = await client.get("/static/css/admin.css")
    assert css_res.status_code == 200
    assert "--primary" in css_res.text

    js_res = await client.get("/static/js/admin.js")
    assert js_res.status_code == 200
    assert "saveQuest" in js_res.text


@pytest.mark.asyncio
async def test_quest_editing_via_api_reflects_in_admin_ui(client: AsyncClient):
    # 1. Update location using PUT /locations/loc_1_shurale
    updated_title = "Дровосек и Шурале (Обновлено через Редактор)"
    updated_layer1 = "Тестовое описание, сохраненное в редакторе квеста."

    update_payload = {
        "title": updated_title,
        "texts": {
            "layer1": updated_layer1,
            "layer2": "Обновленный лор 2.",
            "action_hint": "Новая подсказка",
            "easter_egg": "Новая пасхалка",
        },
    }

    put_res = await client.put("/locations/loc_1_shurale", json=update_payload)
    assert put_res.status_code == 200
    assert put_res.json()["title"] == updated_title

    # 2. View in edit template
    edit_res = await client.get("/admin/quests/loc_1_shurale/edit")
    assert edit_res.status_code == 200
    assert updated_title in edit_res.text
    assert updated_layer1 in edit_res.text

    # 3. View in quests list template
    list_res = await client.get("/admin/quests")
    assert list_res.status_code == 200
    assert updated_title in list_res.text
