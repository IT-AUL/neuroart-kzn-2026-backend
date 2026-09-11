from typing import Any, Dict, List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import LocationAlreadyExistsError, LocationNotFoundError
from app.db.models.location import Location
from app.db.models.progress import UserProgress
from app.schemas.ai import ApproveContentRequest
from app.schemas.location import LocationCreateRequest, LocationUpdateRequest


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

    async def create_location(self, payload: LocationCreateRequest) -> Location:
        stmt = select(Location).where(Location.id == payload.id)
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            raise LocationAlreadyExistsError(location_id=payload.id)

        loc = Location(
            id=payload.id,
            order=payload.order,
            priority=payload.priority,
            title=payload.title,
            mechanic=payload.mechanic,
            mechanic_params=payload.mechanic_params,
            marker=payload.marker.model_dump(),
            model_url=payload.model_url or "",
            models=[m.model_dump() for m in payload.models],
            coordinates=payload.coordinates.model_dump(),
            animations=[a.model_dump() for a in payload.animations],
            texts=payload.texts.model_dump(),
            artifact=payload.artifact.model_dump(),
            next_location_id=payload.next_location_id,
            next_location_order=payload.next_location_order,
            next_location_hint=payload.next_location_hint,
        )
        self.session.add(loc)
        await self.session.commit()
        await self.session.refresh(loc)
        self._enrich_location_models(loc)
        return loc

    async def update_location(self, location_id: str, payload: LocationUpdateRequest) -> Location:
        stmt = select(Location).where(Location.id == location_id)
        result = await self.session.execute(stmt)
        location = result.scalar_one_or_none()

        if not location:
            raise LocationNotFoundError(location_id=location_id)

        update_dict = payload.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(location, field, value)

        await self.session.commit()
        await self.session.refresh(location)
        self._enrich_location_models(location)
        return location

    async def delete_location(self, location_id: str) -> None:
        stmt = select(Location).where(Location.id == location_id)
        result = await self.session.execute(stmt)
        location = result.scalar_one_or_none()

        if not location:
            raise LocationNotFoundError(location_id=location_id)

        # Delete any dependent user progress records
        del_progress_stmt = delete(UserProgress).where(UserProgress.location_id == location_id)
        await self.session.execute(del_progress_stmt)

        await self.session.delete(location)
        await self.session.commit()

    async def apply_approved_content(
        self,
        location_id: str,
        payload: ApproveContentRequest,
    ) -> Location:
        stmt = select(Location).where(Location.id == location_id)
        result = await self.session.execute(stmt)
        location = result.scalar_one_or_none()

        if not location:
            raise LocationNotFoundError(location_id=location_id)

        current_texts = dict(location.texts or {})
        if payload.layer1 is not None:
            current_texts["layer1"] = payload.layer1
        if payload.layer2 is not None:
            current_texts["layer2"] = payload.layer2
        if payload.action_hint is not None:
            current_texts["action_hint"] = payload.action_hint
        if payload.dialogue is not None:
            current_texts["dialogue"] = payload.dialogue
        if payload.easter_egg is not None:
            current_texts["easter_egg"] = payload.easter_egg
        location.texts = current_texts

        current_artifact = dict(location.artifact or {})
        if payload.artifact_name is not None:
            current_artifact["name"] = payload.artifact_name
        if payload.artifact_id is not None:
            current_artifact["id"] = payload.artifact_id
        if payload.artifact_icon is not None:
            current_artifact["icon"] = payload.artifact_icon
        location.artifact = current_artifact

        await self.session.commit()
        await self.session.refresh(location)
        self._enrich_location_models(location)
        return location


