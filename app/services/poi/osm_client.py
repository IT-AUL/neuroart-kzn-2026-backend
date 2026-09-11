import logging
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)

# Overpass API endpoints
OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# Kazan Bounding Box: [south, west, north, east]
KAZAN_BBOX = "55.65,48.85,55.92,49.35"

# Built-in curated landmark dataset for offline resilience and automated test predictability
FALLBACK_KAZAN_POIS: List[Dict[str, Any]] = [
    {
        "osm_id": "node/10000001",
        "osm_type": "node",
        "lat": 55.7984,
        "lon": 49.1051,
        "name": "Мечеть Кул-Шариф",
        "name_en": "Qol Sharif Mosque",
        "name_tt": "Кол Шәриф мәчете",
        "description": "Главная джума-мечеть республики Татарстан и Казани, расположенная на территории Казанского кремля.",
        "tags": {
            "amenity": "place_of_worship",
            "building": "mosque",
            "historic": "heritage",
            "heritage": "UNESCO",
            "wikipedia": "ru:Кул-Шариф",
        },
    },
    {
        "osm_id": "node/10000002",
        "osm_type": "node",
        "lat": 55.7997,
        "lon": 49.1055,
        "name": "Башня Сююмбике",
        "name_en": "Suyumbike Tower",
        "name_tt": "Сөембикә манарасы",
        "description": "Проездная дозорная башня в Казанском кремле. Падающая башня, символ Казани.",
        "tags": {
            "historic": "tower",
            "man_made": "tower",
            "tourism": "attraction",
            "heritage": "UNESCO",
            "photo": "yes",
        },
    },
    {
        "osm_id": "node/10000003",
        "osm_type": "node",
        "lat": 55.7963,
        "lon": 49.1075,
        "name": "Памятник Мусе Джалилю",
        "name_en": "Musa Dzhalil Monument",
        "name_tt": "Муса Җәлилгә һәйкәл",
        "description": "Монументальный комплекс на площади 1 Мая в честь поэта-героя Советского Союза.",
        "tags": {
            "historic": "monument",
            "artwork_type": "statue",
            "highway": "pedestrian",
        },
    },
    {
        "osm_id": "node/10000004",
        "osm_type": "node",
        "lat": 55.7892,
        "lon": 49.1172,
        "name": "Памятник Коту Казанскому",
        "name_en": "Monument to the Cat of Kazan",
        "name_tt": "Казан песие һәйкәле",
        "description": "Металлическая скульптурная композиция на пешеходной улице Баумана в честь казанских котов-мышеловов.",
        "tags": {
            "historic": "monument",
            "artwork_type": "statue",
            "tourism": "attraction",
            "highway": "pedestrian",
        },
    },
    {
        "osm_id": "node/10000005",
        "osm_type": "node",
        "lat": 55.7853,
        "lon": 49.1178,
        "name": "Татарский театр драмы имени Галиасгара Камала",
        "name_en": "Galiasgar Kamal Tatar Academic Theatre",
        "name_tt": "Галиәсгар Камал исемендәге Татар дәүләт академия театры",
        "description": "Старейший национальный театр Татарстана на берегу живописного озера Нижний Кабан.",
        "tags": {
            "amenity": "theatre",
            "tourism": "attraction",
            "waterway": "riverbank",
        },
    },
    {
        "osm_id": "node/10000006",
        "osm_type": "node",
        "lat": 55.7820,
        "lon": 49.1180,
        "name": "Набережная озера Нижний Кабан",
        "name_en": "Lower Lake Kaban Promenade",
        "name_tt": "Түбән Кабан күле яр буе",
        "description": "Обустроенная пешеходная набережная с каскадами фонтанов и арт-объектами на озере Кабан.",
        "tags": {
            "leisure": "park",
            "tourism": "attraction",
            "waterway": "riverbank",
            "pedestrian": "yes",
        },
    },
    {
        "osm_id": "node/10000007",
        "osm_type": "node",
        "lat": 55.7801,
        "lon": 49.1189,
        "name": "Старо-Татарская слобода",
        "name_en": "Old Tatar Settlement",
        "name_tt": "Иске Татар бистәсе",
        "description": "Исторический архитектурный ансамбль деревянных и каменных усадеб татарских купцов и мечетей.",
        "tags": {
            "historic": "district",
            "tourism": "attraction",
            "highway": "pedestrian",
        },
    },
    {
        "osm_id": "node/10000008",
        "osm_type": "node",
        "lat": 55.7950,
        "lon": 49.1028,
        "name": "Скульптура Дракона Зилант у метро Кремлевская",
        "name_en": "Zilant Dragon Sculpture",
        "name_tt": "Зилант сыны",
        "description": "Кованая скульптура мифического крылатого змея Зиланта, покровителя и символа Казани.",
        "tags": {
            "historic": "monument",
            "artwork_type": "sculpture",
            "tourism": "attraction",
        },
    },
    {
        "osm_id": "node/10000009",
        "osm_type": "node",
        "lat": 55.7876,
        "lon": 49.1235,
        "name": "Колокольня Богоявленского собора",
        "name_en": "Epiphany Bell Tower",
        "name_tt": "Богоявление соборы кыңгыравы",
        "description": "Знаменитая высотная краснокирпичная колокольня на улице Баумана со смотровой площадкой.",
        "tags": {
            "historic": "tower",
            "tourism": "viewpoint",
            "building": "tower",
        },
    },
    {
        "osm_id": "node/10000010",
        "osm_type": "node",
        "lat": 55.7925,
        "lon": 49.1170,
        "name": "Парк 'Черное озеро'",
        "name_en": "Black Lake Park",
        "name_tt": "Черек күл паркы",
        "description": "Городской парк в историческом центре Казани с аркой влюбленных и прудом.",
        "tags": {
            "leisure": "park",
            "tourism": "attraction",
            "highway": "pedestrian",
        },
    },
]


class OsmClient:
    """
    OpenStreetMap / Overpass API client for querying and extracting POIs.
    """

    @classmethod
    def build_overpass_query(cls, bbox: str = KAZAN_BBOX) -> str:
        """
        Constructs Overpass QL query targeting cultural, historical, and tourism POIs.
        """
        return f"""
        [out:json][timeout:25];
        (
          node["historic"]({bbox});
          way["historic"]({bbox});
          node["tourism"~"museum|attraction|gallery|viewpoint"]({bbox});
          way["tourism"~"museum|attraction|gallery|viewpoint"]({bbox});
          node["amenity"~"theatre|arts_centre"]({bbox});
          way["amenity"~"theatre|arts_centre"]({bbox});
          node["leisure"~"park|garden"]({bbox});
          way["leisure"~"park|garden"]({bbox});
        );
        out center tags 200;
        """

    @classmethod
    async def fetch_pois(
        cls,
        bbox: str = KAZAN_BBOX,
        force_remote: bool = False,
        timeout_seconds: float = 12.0,
    ) -> List[Dict[str, Any]]:
        """
        Fetches POIs from Overpass API. If remote query fails or force_remote is False,
        returns the curated built-in Kazan dataset to guarantee uptime and speed.
        """
        if force_remote:
            query = cls.build_overpass_query(bbox)
            for server_url in OVERPASS_SERVERS:
                try:
                    logger.info("Querying Overpass server: %s", server_url)
                    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                        response = await client.post(server_url, data={"data": query})
                        if response.status_code == 200:
                            data = response.json()
                            elements = data.get("elements", [])
                            parsed = cls._parse_overpass_elements(elements)
                            if parsed:
                                logger.info("Successfully fetched %d POIs from Overpass", len(parsed))
                                return parsed
                        else:
                            logger.warning("Overpass error %d from %s", response.status_code, server_url)
                except Exception as exc:
                    logger.warning("Failed to connect to Overpass server %s: %s", server_url, exc)

        logger.info("Using built-in curated Kazan POI dataset (%d points)", len(FALLBACK_KAZAN_POIS))
        return list(FALLBACK_KAZAN_POIS)

    @classmethod
    def _parse_overpass_elements(cls, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name:ru") or tags.get("name") or tags.get("name:tt") or tags.get("name:en")
            if not name:
                continue

            el_type = el.get("type", "node")
            el_id = el.get("id")
            osm_id = f"{el_type}/{el_id}"

            lat: Optional[float] = None
            lon: Optional[float] = None

            if "lat" in el and "lon" in el:
                lat = float(el["lat"])
                lon = float(el["lon"])
            elif "center" in el:
                lat = float(el["center"]["lat"])
                lon = float(el["center"]["lon"])

            if lat is None or lon is None:
                continue

            description = tags.get("description") or tags.get("description:ru")
            if not description and "wikipedia" in tags:
                description = f"Объект из Википедии: {tags['wikipedia']}"

            results.append({
                "osm_id": osm_id,
                "osm_type": el_type,
                "lat": lat,
                "lon": lon,
                "name": name,
                "name_en": tags.get("name:en"),
                "name_tt": tags.get("name:tt"),
                "description": description,
                "tags": tags,
            })

        return results
