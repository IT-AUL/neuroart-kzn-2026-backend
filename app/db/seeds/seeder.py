import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.location import Location
from app.db.seeds.initial_data import INITIAL_LOCATIONS

logger = logging.getLogger(__name__)


async def seed_locations(session: AsyncSession) -> None:
    """Idempotently seed the initial route locations if not already present."""
    for item in INITIAL_LOCATIONS:
        stmt = select(Location).where(Location.id == item["id"])
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            loc = Location(
                id=item["id"],
                order=item["order"],
                priority=item["priority"],
                title=item["title"],
                mechanic=item["mechanic"],
                mechanic_params=item["mechanic_params"],
                marker=item["marker"],
                model_url=item["model_url"],
                coordinates=item["coordinates"],
                animations=item["animations"],
                texts=item["texts"],
                artifact=item["artifact"],
            )
            session.add(loc)
            logger.info("Seeding location: %s (%s)", loc.id, loc.title)

    await session.commit()
