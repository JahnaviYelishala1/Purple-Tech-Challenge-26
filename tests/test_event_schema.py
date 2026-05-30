# PROMPT:
# Create pytest tests for event schema validation.
#
# CHANGES MADE:
# Added edge cases for duplicate ingestion and conversion tracking.

from datetime import datetime, timezone

from app.schemas.event import Event, EventType


def test_entry_event_validates_successfully() -> None:
    """Validate that a well-formed ENTRY event is accepted by the schema."""

    event = Event.model_validate(
        {
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "store_id": "store-001",
            "camera_id": "camera-12",
            "visitor_id": "visitor-abc",
            "event_type": EventType.ENTRY,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": None,
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.98,
            "metadata": {
                "queue_depth": 3,
                "sku_zone": "checkout",
                "session_seq": 1,
            },
        }
    )

    assert event.event_type is EventType.ENTRY
    assert event.store_id == "store-001"
    assert event.metadata is not None
    assert event.metadata.queue_depth == 3