from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """Supported retail analytics event types."""

    ENTRY = "ENTRY"
    EXIT = "EXIT"
    ZONE_ENTER = "ZONE_ENTER"
    ZONE_EXIT = "ZONE_EXIT"
    ZONE_DWELL = "ZONE_DWELL"
    BILLING_QUEUE_JOIN = "BILLING_QUEUE_JOIN"
    BILLING_QUEUE_ABANDON = "BILLING_QUEUE_ABANDON"
    REENTRY = "REENTRY"


class EventMetadata(BaseModel):
    """Optional event metadata for enriched ingestion payloads."""

    queue_depth: int | None = Field(default=None, ge=0)
    sku_zone: str | None = Field(default=None, max_length=100)
    session_seq: int | None = Field(default=None, ge=0)

    model_config = ConfigDict(extra="forbid")


class Event(BaseModel):
    """Core ingestion schema for store intelligence events."""

    event_id: UUID
    store_id: str = Field(min_length=1, max_length=100)
    camera_id: str = Field(min_length=1, max_length=100)
    visitor_id: str = Field(min_length=1, max_length=100)
    event_type: EventType
    timestamp: datetime
    zone_id: str | None = Field(default=None, max_length=100)
    dwell_ms: int = Field(default=0, ge=0)
    is_staff: bool
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: EventMetadata | None = None

    model_config = ConfigDict(extra="forbid")