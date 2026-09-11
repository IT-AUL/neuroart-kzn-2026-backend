from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Poi(Base):
    __tablename__ = "pois"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    osm_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    osm_type: Mapped[str] = mapped_column(String(16), nullable=False, default="node")
    
    # Display naming
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_tt: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Spatial coordinates
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)

    # Categories and tags
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    # Auto-tagging suggestions before admin review
    proposed_category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    proposed_tags: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    # Complete raw tags from OSM (for diagnostics and rich metadata)
    raw_osm_tags: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Contextual description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Human-in-the-Loop review status: "pending", "approved", "rejected"
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class PoiSyncLog(Base):
    __tablename__ = "poi_sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    points_scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    area_name: Mapped[str] = mapped_column(String(128), nullable=False, default="Kazan")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
