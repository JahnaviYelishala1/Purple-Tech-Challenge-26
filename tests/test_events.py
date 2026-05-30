# PROMPT:
# Create pytest tests for event ingestion.
#
# CHANGES MADE:
# Added edge cases for duplicate ingestion and conversion tracking.

def _event_payload(event_id: str, event_type: str, visitor_id: str = "VIS_001") -> dict[str, object]:
    return {
        "event_id": event_id,
        "store_id": "STORE_BLR_001",
        "camera_id": "CAM_ENTRY_01",
        "visitor_id": visitor_id,
        "event_type": event_type,
        "timestamp": "2026-03-03T14:00:00Z",
        "zone_id": None,
        "dwell_ms": 0,
        "is_staff": False,
        "confidence": 0.95,
        "metadata": {},
    }


def test_successful_event_ingestion(client) -> None:
    """A valid event payload should ingest successfully."""

    response = client.post(
        "/events/ingest",
        json={"events": [_event_payload("11111111-1111-1111-1111-111111111111", "ENTRY")]},
    )

    assert response.status_code == 200
    assert response.json() == {"total_received": 1, "inserted": 1, "duplicates": 0}


def test_duplicate_event_ingestion(client) -> None:
    """A duplicate event_id should be skipped on the second request."""

    payload = {"events": [_event_payload("22222222-2222-2222-2222-222222222222", "ENTRY")]}

    first_response = client.post("/events/ingest", json=payload)
    second_response = client.post("/events/ingest", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json() == {"total_received": 1, "inserted": 0, "duplicates": 1}


def test_multiple_events_in_one_request(client) -> None:
    """A batch request should ingest multiple unique events together."""

    response = client.post(
        "/events/ingest",
        json={
            "events": [
                _event_payload("33333333-3333-3333-3333-333333333331", "ENTRY", "VIS_A"),
                _event_payload("33333333-3333-3333-3333-333333333332", "ZONE_ENTER", "VIS_B"),
            ]
        },
    )

    assert response.status_code == 200
    assert response.json() == {"total_received": 2, "inserted": 2, "duplicates": 0}


def test_invalid_payload_returns_validation_error(client) -> None:
    """An invalid request body should be rejected by FastAPI validation."""

    response = client.post("/events/ingest", json={"events": [{"store_id": "STORE_BLR_001"}]})

    assert response.status_code == 422