from typing import Any, Dict, List, Optional
from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    mechanic: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Structured JSON fields
    mechanic_params: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    marker: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    model_url: Mapped[str] = mapped_column(String(512), nullable=False)
    models: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    coordinates: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    animations: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    texts: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    artifact: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Route navigation
    next_location_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    next_location_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    next_location_hint: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

