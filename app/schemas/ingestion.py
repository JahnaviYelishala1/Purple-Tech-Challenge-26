from pydantic import BaseModel, Field

from app.schemas.event import Event


class EventIngestRequest(BaseModel):
    """Request body for bulk ingestion of validated retail events."""

    events: list[Event] = Field(min_length=1, max_length=500)