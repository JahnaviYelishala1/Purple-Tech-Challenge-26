# PROMPT:
# Create pytest tests for store pipeline status.

from datetime import datetime, timezone

from app.models.event import Event
from pipeline.camera_roles import camera_ids_for_role, role_label


def test_pipeline_status_returns_camera_and_last_event_proof(client, db_session) -> None:
    """The pipeline status endpoint should surface CCTV camera health and track IDs."""

    entrance_camera = camera_ids_for_role("ENTRANCE")[0]
    billing_camera = camera_ids_for_role("BILLING")[0]

    db_session.add_all(
        [
            Event(
                event_id="status-entry-1",
                store_id="STORE_BLR_001",
                camera_id=entrance_camera,
                visitor_id="track_24",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 13, 0, tzinfo=timezone.utc),
                zone_id="entrance",
                dwell_ms=0,
                is_staff=False,
                confidence=0.96,
            ),
            Event(
                event_id="status-billing-1",
                store_id="STORE_BLR_001",
                camera_id=billing_camera,
                visitor_id="track_6",
                event_type="BILLING_QUEUE_JOIN",
                timestamp=datetime(2026, 3, 3, 13, 5, tzinfo=timezone.utc),
                zone_id="billing",
                dwell_ms=0,
                is_staff=False,
                confidence=0.97,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/stores/STORE_BLR_001/pipeline-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cameras"][0]["camera_id"] == entrance_camera
    assert payload["cameras"][0]["label"] == f"{entrance_camera} ({role_label('ENTRANCE')})"
    assert payload["cameras"][0]["status"] == "Active"
    assert payload["cameras"][0]["last_event_id"] == "status-entry-1"
    assert payload["cameras"][0]["last_track_id"] == "track_24"
    assert payload["cameras"][0]["last_event_type"] == "ENTRY"
    assert str(payload["cameras"][0]["last_seen"]).startswith("2026-03-03T13:00:00")

    assert payload["cameras"][1]["camera_id"] == billing_camera
    assert payload["cameras"][1]["label"] == f"{billing_camera} ({role_label('BILLING')})"
    assert payload["cameras"][1]["status"] == "Active"
    assert payload["cameras"][1]["last_event_id"] == "status-billing-1"
    assert payload["cameras"][1]["last_track_id"] == "track_6"
    assert payload["cameras"][1]["last_event_type"] == "BILLING_QUEUE_JOIN"
    assert str(payload["cameras"][1]["last_seen"]).startswith("2026-03-03T13:05:00")

    assert payload["last_entry_event"]["track_id"] == "track_24"
    assert payload["last_billing_event"]["track_id"] == "track_6"