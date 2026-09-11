from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import LocationNotFoundError
from app.db.models.location import Location


class LocationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _resolve_model_url(self, model_url: str) -> str:
        """If Yandex S3 base URL is configured and model_url is relative, prefix it."""
        if settings.YANDEX_S3_PUBLIC_BASE_URL and not (
            model_url.startswith("http://") or model_url.startswith("https://")
        ):
            base = settings.YANDEX_S3_PUBLIC_BASE_URL.rstrip("/")
            clean_url = model_url.lstrip("/")
            return f"{base}/{clean_url}"
        return model_url

    def _enrich_location_models(self, loc: Location) -> None:
        """Resolve primary model_url and all sub-model URLs."""
        loc.model_url = self._resolve_model_url(loc.model_url)
        if loc.models and isinstance(loc.models, list):
            enriched_models = []
            for item in loc.models:
                if isinstance(item, dict) and "url" in item:
                    item_copy = dict(item)
                    item_copy["url"] = self._resolve_model_url(item_copy["url"])
                    enriched_models.append(item_copy)
                else:
                    enriched_models.append(item)
            loc.models = enriched_models

    async def get_all_locations(self) -> List[Location]:
        stmt = select(Location).order_by(Location.order.asc())
        result = await self.session.execute(stmt)
        locations = list(result.scalars().all())

        for loc in locations:
            self._enrich_location_models(loc)
        return locations

    async def get_location_by_id(self, location_id: str) -> Location:
        stmt = select(Location).where(Location.id == location_id)
        result = await self.session.execute(stmt)
        location = result.scalar_one_or_none()

        if not location:
            raise LocationNotFoundError(location_id=location_id)

        self._enrich_location_models(location)
        return location

