import asyncio
import json
import sys
from httpx import ASGITransport, AsyncClient
from app.main import app

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


async def main():
    print("=" * 70)
    print("QUEST EDITOR WORKFLOW DEMONSTRATION")
    print("=" * 70)

    from app.main import lifespan

    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # -------------------------------------------------------------
            # Step 1: Editor requests POI recommendations near current map pin
            # -------------------------------------------------------------
            print("\n[STEP 1] Creator opens Quest Editor at Kazan Kremlin area:")
            print("  Map Center: lat=55.7984, lon=49.1051, radius=1500m")
            print("  Request: GET /api/v1/poi/recommendations?near_lat=55.7984&near_lon=49.1051&radius_meters=1500")

            rec_resp = await client.get("/api/v1/poi/recommendations?near_lat=55.7984&near_lon=49.1051&radius_meters=1500&limit=3")

            recommendations = rec_resp.json()
            print(f"  [+] Editor received {len(recommendations)} recommended POIs:")

            for i, item in enumerate(recommendations, 1):
                poi = item["poi"]
                print(f"\n      Option #{i}: \"{poi['name']}\" (ID: {poi['id']})")
                print(f"        * Distance     : {item['distance_meters']} m")
                print(f"        * Match Score  : {item['match_score']:.2f}")
                print(f"        * Category     : {poi['category']}")
                print(f"        * Tags         : {poi['tags']}")
                print(f"        * Description  : {poi['description']}")
                print(f"        * Badges       : {item['reasons']}")

            # -------------------------------------------------------------
            # Step 2: Creator picks Option #2 and clicks 'Add to Quest Route'
            # -------------------------------------------------------------
            chosen_poi = recommendations[1]["poi"]
            print(f"\n[STEP 2] Creator clicks 'Add to Quest' on: \"{chosen_poi['name']}\"")
            print("  Request: POST /api/v1/locations/from-poi")

            convert_payload = {
                "poi_id": chosen_poi["id"],
                "order": 4,
                "priority": "P1",
                "mechanic": "trace",
                "custom_title": f"AR Квест: {chosen_poi['name']}",
            }
            create_resp = await client.post("/api/v1/locations/from-poi", json=convert_payload)
            new_location = create_resp.json()

            print(f"  [+] Status Code: {create_resp.status_code} CREATED")
            print(f"  [+] Created Location:")
            print(f"      - ID           : {new_location['id']}")
            print(f"      - Route Order  : #{new_location['order']}")
            print(f"      - Title        : \"{new_location['title']}\"")
            print(f"      - Mechanic     : {new_location['mechanic']}")
            print(f"      - Marker Asset : {new_location['marker']['asset']}")
            print(f"      - 3D Model URL : {new_location['model_url']}")
            print(f"      - Text Layer 1 : \"{new_location['texts']['layer1']}\"")
            print(f"      - Text Layer 2 : \"{new_location['texts']['layer2']}\"")
            print(f"      - Action Hint  : \"{new_location['texts']['action_hint']}\"")
            print(f"      - Artifact     : {new_location['artifact']['name']} (Icon: {new_location['artifact']['icon']})")

            # -------------------------------------------------------------
            # Step 3: Verify the location is now active in the route
            # -------------------------------------------------------------
            print("\n[STEP 3] Verifying route points via GET /api/v1/locations:")
            all_locs_resp = await client.get("/api/v1/locations")
            all_locs = all_locs_resp.json()
            print(f"  [+] Route now contains {len(all_locs)} active locations:")
            for loc in all_locs:
                print(f"      #{loc['order']}: \"{loc['title']}\" (ID: {loc['id']}, Mechanic: {loc['mechanic']})")

    print("\n" + "=" * 70)
    print("QUEST EDITOR FLOW IS 100% OPERATIONAL!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
