import re
from typing import Any, Dict, List, Tuple

# Supported Primary Categories
CATEGORY_MONUMENT = "monument"
CATEGORY_MUSEUM_CULTURE = "museum_culture"
CATEGORY_HISTORIC_QUARTER = "historic_quarter"
CATEGORY_NATURE_VIEW = "nature_view"
CATEGORY_FOLKLORE_LEGENDS = "folklore_legends"
CATEGORY_ARCHITECTURE_HERITAGE = "architecture_heritage"
CATEGORY_OTHER = "other"

# Supported Semantic Tags
TAG_TATAR_CULTURE = "tatar_culture"
TAG_UNESCO = "unesco"
TAG_AR_FRIENDLY = "ar_friendly"
TAG_WATERFRONT = "waterfront"
TAG_PHOTO_SPOT = "photo_spot"
TAG_FAMILY_FRIENDLY = "family_friendly"

TATAR_CULTURE_KEYWORDS = {
    "татар", "тука", "джалил", "кремл", "казан", "зилант", "шурале",
    "мечет", "кул-шариф", "кул шариф", "кабан", "су анасы", "алтын",
    "марджан", "бауман", "слобода", "батыр", "сабанту", "сяюмбик",
    "сююмбик", "чай", "чак-чак", "чак чак", "эчпочмак", "татарстан"
}

FOLKLORE_KEYWORDS = {
    "зилант", "шурале", "су анасы", "кот казанск", "алтынчеч",
    "батыр", "легенд", "миф", "сказк", "фольклор", "дракон"
}

UNESCO_KEYWORDS = {
    "кремл", "сююмбик", "кул-шариф", "кул шариф", "благовещенск", "спасск"
}

WATERFRONT_KEYWORDS = {
    "кабан", "булак", "казанк", "волг", "набережн", "мост", "озер", "рек"
}

AR_FRIENDLY_KEYWORDS = {
    "площад", "парк", "сквер", "улиц", "бауман", "пешеходн", "набережн", "сад"
}



class PoiTagEngine:
    """
    Automated classification and tagging engine for OpenStreetMap POIs.
    Translates raw OSM key-value pairs and entity names into standardized
    categories and semantic tags for the quest editor.
    """

    @classmethod
    def classify(cls, name: str, osm_tags: Dict[str, Any]) -> Tuple[str, List[str], float]:
        """
        Classifies an OSM POI and returns (category, tags, confidence_score).
        """
        tags: List[str] = []
        name_lower = (name or "").lower()
        desc_lower = (osm_tags.get("description", "") or "").lower()
        combined_text = f"{name_lower} {desc_lower}"

        category, base_conf = cls._determine_category(osm_tags, combined_text)

        # 1. Folklore & Legends check (upgrades category if strong match)
        if any(kw in combined_text for kw in FOLKLORE_KEYWORDS):
            category = CATEGORY_FOLKLORE_LEGENDS
            tags.append(TAG_FAMILY_FRIENDLY)
            base_conf = max(base_conf, 0.9)

        # 2. Semantic Tag: Tatar Culture
        if any(kw in combined_text for kw in TATAR_CULTURE_KEYWORDS) or "name:tt" in osm_tags:
            tags.append(TAG_TATAR_CULTURE)

        # 3. Semantic Tag: UNESCO Heritage
        heritage = osm_tags.get("heritage", "") or osm_tags.get("heritage:operator", "")
        if "unesco" in heritage.lower() or any(kw in combined_text for kw in UNESCO_KEYWORDS):
            tags.append(TAG_UNESCO)

        # 4. Semantic Tag: Waterfront
        if any(kw in combined_text for kw in WATERFRONT_KEYWORDS) or osm_tags.get("waterway"):
            tags.append(TAG_WATERFRONT)

        # 5. Semantic Tag: AR Friendly / Pedestrian
        highway = osm_tags.get("highway", "")
        pedestrian = osm_tags.get("pedestrian", "")
        if highway == "pedestrian" or pedestrian == "yes" or any(kw in combined_text for kw in AR_FRIENDLY_KEYWORDS):
            tags.append(TAG_AR_FRIENDLY)

        # 6. Semantic Tag: Photo Spot
        if osm_tags.get("tourism") == "viewpoint" or osm_tags.get("photo") or category in {CATEGORY_MONUMENT, CATEGORY_ARCHITECTURE_HERITAGE}:
            tags.append(TAG_PHOTO_SPOT)

        # Deduplicate tags
        unique_tags = sorted(list(set(tags)))
        return category, unique_tags, round(base_conf, 2)

    @classmethod
    def _determine_category(cls, osm_tags: Dict[str, Any], text: str) -> Tuple[str, float]:
        historic = osm_tags.get("historic", "")
        tourism = osm_tags.get("tourism", "")
        amenity = osm_tags.get("amenity", "")
        leisure = osm_tags.get("leisure", "")
        building = osm_tags.get("building", "")

        # Historic monuments and memorials
        if historic in {"monument", "memorial", "statue"} or osm_tags.get("artwork_type") in {"statue", "sculpture"}:
            return CATEGORY_MONUMENT, 0.95

        # Museums, galleries, theatres
        if tourism in {"museum", "gallery"} or amenity in {"theatre", "arts_centre"}:
            return CATEGORY_MUSEUM_CULTURE, 0.95

        # Historic districts, quarters, manors, ancient towers
        if historic in {"district", "heritage", "manor", "city_gate", "castle", "fort", "archaeological_site"} or "слобода" in text or "кремль" in text:
            return CATEGORY_HISTORIC_QUARTER, 0.90

        # Architecture & notable historical buildings
        if historic in {"building", "tower"} or building in {"cathedral", "church", "mosque", "temple", "tower"}:
            return CATEGORY_ARCHITECTURE_HERITAGE, 0.85

        # Parks, gardens, viewpoints
        if leisure in {"park", "garden"} or tourism == "viewpoint":
            return CATEGORY_NATURE_VIEW, 0.90

        # Generic tourism attraction
        if tourism == "attraction":
            if any(w in text for w in ["памятник", "бюст", "скульптур", "мемориал"]):
                return CATEGORY_MONUMENT, 0.85
            if any(w in text for w in ["музей", "галере"]):
                return CATEGORY_MUSEUM_CULTURE, 0.85
            return CATEGORY_HISTORIC_QUARTER, 0.75

        # Fallback based on keywords in name
        if any(w in text for w in ["памятник", "монумент", "стела", "скульптур"]):
            return CATEGORY_MONUMENT, 0.80
        if any(w in text for w in ["музей", "театр", "выставк"]):
            return CATEGORY_MUSEUM_CULTURE, 0.80
        if any(w in text for w in ["парк", "сквер", "сад", "озеро"]):
            return CATEGORY_NATURE_VIEW, 0.80
        if any(w in text for w in ["башня", "ворота", "собор", "мечеть"]):
            return CATEGORY_ARCHITECTURE_HERITAGE, 0.80

        return CATEGORY_OTHER, 0.50
