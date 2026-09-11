import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_location_crud_lifecycle(client: AsyncClient):
    # 1. Create a new location
    new_loc_payload = {
        "id": "loc_4_kaban_lake",
        "order": 4,
        "priority": "P1",
        "title": "Озеро Кабан и водяная Су анасы",
        "mechanic": "none",
        "mechanic_params": {},
        "marker": {"type": "image", "asset": "marker_kaban.png"},
        "model_url": "models/loc4_su_anasy.glb",
        "models": [
            {
                "id": "water_surface",
                "name": "Гладь озера Кабан",
                "url": "models/loc4_lake.glb",
                "is_primary": True,
            },
            {
                "id": "su_anasy",
                "name": "Су анасы",
                "url": "models/loc4_su_anasy_char.glb",
                "is_primary": False,
            },
        ],
        "coordinates": {"x": 0.0, "y": 0.0, "z": 0.0, "scale": 1.0},
        "animations": [
            {"id": 0, "name": "water_ripples"},
            {"id": 1, "name": "su_anasy_splash"},
        ],
        "texts": {
            "layer1": "Озеро Кабан — легендарная водная система в центре Казани.",
            "layer2": "По преданиям, на дне озера сокрыты ханские сокровища, охраняемые духами воды.",
            "action_hint": "Коснитесь глади воды, чтобы найти золотой гребень",
            "dialogue": [
                {
                    "speaker": "Су анасы",
                    "text": "Кто тревожит покой древних вод?",
                    "trigger": "appear",
                }
            ],
            "easter_egg": "Легенда гласит: тот, кто вернёт золотой гребень водяной, обретёт удачу.",
        },
        "artifact": {
            "id": "golden_comb",
            "name": "Золотой гребень",
            "icon": "icons/comb.png",
        },
        "next_location_id": None,
        "next_location_order": None,
        "next_location_hint": "Конец расширенного маршрута",
    }

    create_res = await client.post("/locations", json=new_loc_payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["id"] == "loc_4_kaban_lake"
    assert created_data["title"] == "Озеро Кабан и водяная Су анасы"
    assert len(created_data["models"]) == 2

    # 2. Duplicate create fails with 409 Conflict
    dup_res = await client.post("/locations", json=new_loc_payload)
    assert dup_res.status_code == 409

    # 3. Read the created location
    get_res = await client.get("/locations/loc_4_kaban_lake")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Озеро Кабан и водяная Су анасы"

    # 4. Update the location
    update_payload = {
        "title": "Озеро Кабан: Тайна Золотого Гребня",
        "priority": "P0",
    }
    put_res = await client.put("/locations/loc_4_kaban_lake", json=update_payload)
    assert put_res.status_code == 200
    updated_data = put_res.json()
    assert updated_data["title"] == "Озеро Кабан: Тайна Золотого Гребня"
    assert updated_data["priority"] == "P0"

    # 5. Delete the location
    del_res = await client.delete("/locations/loc_4_kaban_lake")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # 6. Verify it is gone
    get_after_del = await client.get("/locations/loc_4_kaban_lake")
    assert get_after_del.status_code == 404
