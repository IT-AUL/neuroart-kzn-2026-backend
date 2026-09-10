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

    async def get_all_locations(self) -> List[Location]:
        stmt = select(Location).order_by(Location.order.asc())
        result = await self.session.execute(stmt)
        locations = list(result.scalars().all())

        # Optionally enrich model_url if public base is set
        for loc in locations:
            loc.model_url = self._resolve_model_url(loc.model_url)
        return locations

    async def get_location_by_id(self, location_id: str) -> Location:
        stmt = select(Location).where(Location.id == location_id)
        result = await self.session.execute(stmt)
        location = result.scalar_one_or_none()

        if not location:
            raise LocationNotFoundError(location_id=location_id)

        location.model_url = self._resolve_model_url(location.model_url)
        return location
