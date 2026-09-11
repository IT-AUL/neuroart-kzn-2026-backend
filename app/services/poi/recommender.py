import math
from typing import Any, Dict, List, Optional, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.poi import Poi
from app.schemas.poi import PoiRecommendationItem, PoiResponse


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates great-circle distance between two points in meters using Haversine formula.
    """
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class PoiRecommender:
    """
    Intelligent recommendation engine for quest creators in the editor.
    Ranks POIs based on spatial proximity, thematic tag overlap,
    curation approval, and contextual relevance.
    """

    @classmethod
    async def recommend(
        cls,
        session: AsyncSession,
        near_lat: Optional[float] = None,
        near_lon: Optional[float] = None,
        radius_meters: float = 2500.0,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        status: str = "approved",
        exclude_ids: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[PoiRecommendationItem]:
        query = select(Poi)

        # Status filter
        if status != "all":
            query = query.where(Poi.status == status)

        # Category filter
        if category:
            query = query.where(Poi.category == category)

        # Name / Description search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (Poi.name.ilike(search_pattern)) | (Poi.description.ilike(search_pattern))
            )

        res = await session.execute(query)
        all_pois = res.scalars().all()

        exclude_set: Set[str] = set(exclude_ids or [])
        target_tags: Set[str] = set(t.strip().lower() for t in (tags or []) if t.strip())

        candidates: List[PoiRecommendationItem] = []

        for poi in all_pois:
            if poi.id in exclude_set or poi.osm_id in exclude_set:
                continue

            dist: Optional[float] = None
            reasons: List[str] = []
            score = 0.0

            # 1. Spatial proximity calculation
            if near_lat is not None and near_lon is not None:
                dist = haversine_distance_meters(near_lat, near_lon, poi.latitude, poi.longitude)
                if dist > radius_meters and not search:
                    continue  # Skip outside radius unless explicitly searched

                # Distance score decay
                dist_score = max(0.0, 1.0 - (dist / radius_meters))
                score += 0.40 * dist_score
                if dist <= 300:
                    reasons.append(f"В шаговой доступности ({int(dist)} м)")
                elif dist <= 1000:
                    reasons.append(f"Рядом по маршруту ({int(dist)} м)")
                else:
                    reasons.append(f"В радиусе {int(dist / 1000 * 10) / 10} км")
            else:
                score += 0.20  # Neutral baseline if no coordinates specified

            # 2. Tag overlap scoring
            poi_tags = set(t.lower() for t in (poi.tags or []))
            if target_tags:
                matched_tags = target_tags.intersection(poi_tags)
                tag_ratio = len(matched_tags) / len(target_tags)
                score += 0.35 * tag_ratio
                for mt in matched_tags:
                    reasons.append(f"Тег: #{mt}")
            elif poi_tags:
                score += 0.10

            # 3. Category match
            if category and poi.category == category:
                score += 0.15
                reasons.append(f"Категория: {category}")

            # 4. Approval status bonus
            if poi.status == "approved":
                score += 0.15
                reasons.append("Проверено модератором")
            elif poi.status == "pending":
                score += 0.05

            # 5. Richness bonus (description / wiki)
            if poi.description:
                score += 0.05

            candidates.append(
                PoiRecommendationItem(
                    poi=PoiResponse.model_validate(poi),
                    distance_meters=round(dist, 1) if dist is not None else None,
                    match_score=round(score, 3),
                    reasons=reasons,
                )
            )

        # Sort candidates descending by match_score, then ascending by distance
        candidates.sort(
            key=lambda item: (
                -item.match_score,
                item.distance_meters if item.distance_meters is not None else float("inf"),
            )
        )

        return candidates[:limit]
