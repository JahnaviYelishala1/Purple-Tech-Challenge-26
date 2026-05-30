from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CameraPipelineStatus(BaseModel):
    camera_id: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=100)
    active: bool
    status: str = Field(min_length=1, max_length=50)
    last_event_id: str | None = Field(default=None, max_length=100)
    last_track_id: str | None = Field(default=None, max_length=100)
    last_event_type: str | None = Field(default=None, max_length=50)
    last_seen: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PipelineEventSnapshot(BaseModel):
    event_id: str = Field(min_length=1, max_length=100)
    track_id: str = Field(min_length=1, max_length=100)
    camera_id: str = Field(min_length=1, max_length=100)
    event_type: str = Field(min_length=1, max_length=50)
    last_seen: datetime | None = None


class StorePipelineStatusResponse(BaseModel):
    cameras: list[CameraPipelineStatus]
    last_entry_event: PipelineEventSnapshot | None = None
    last_billing_event: PipelineEventSnapshot | None = None
    activity_summary: dict[str, int] = Field(default_factory=dict)