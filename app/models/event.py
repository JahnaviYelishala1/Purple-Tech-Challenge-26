from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Event(Base):
    """SQLAlchemy model for retail analytics ingestion events."""

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_store_type_timestamp", "store_id", "event_type", "timestamp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    store_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    camera_id: Mapped[str] = mapped_column(String(100), nullable=False)
    visitor_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    zone_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dwell_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_staff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    queue_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sku_zone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    session_seq: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        """Return a concise string representation for debugging."""

        return (
            f"Event(id={self.id!r}, event_id={self.event_id!r}, store_id={self.store_id!r}, "
            f"event_type={self.event_type!r}, timestamp={self.timestamp!r})"
        )