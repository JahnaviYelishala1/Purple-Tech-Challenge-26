from datetime import datetime, timezone

from app.models.event import Event
from app.models.session import VisitorSession
from pipeline.camera_roles import camera_ids_for_role


def _payload(event_id: str, event_type: str, timestamp: datetime, camera_id: str) -> dict[str, object]:
    return {
        "event_id": event_id,
        "store_id": "STORE_BLR_001",
        "camera_id": camera_id,
        "visitor_id": "VIS_EXIT_001",
        "event_type": event_type,
        "timestamp": timestamp.isoformat(),
        "zone_id": "exit" if event_type == "EXIT" else None,
        "dwell_ms": 0,
        "is_staff": False,
        "confidence": 0.95,
        "metadata": {},
    }


def test_exit_events_close_sessions_and_update_duration(client, db_session) -> None:
    """An EXIT event should be accepted, close the session, and reflect in metrics."""

    entrance_camera = camera_ids_for_role("ENTRANCE")[0]
    exit_cameras = camera_ids_for_role("EXIT")
    assert exit_cameras, "EXIT role must be configured"
    exit_camera = exit_cameras[0]

    start_time = datetime(2026, 3, 3, 14, 0, tzinfo=timezone.utc)
    exit_time = datetime(2026, 3, 3, 14, 15, tzinfo=timezone.utc)

    entry_response = client.post(
        "/events/ingest",
        json={"events": [_payload("44444444-4444-4444-4444-444444444444", "ENTRY", start_time, entrance_camera)]},
    )
    exit_response = client.post(
        "/events/ingest",
        json={"events": [_payload("55555555-5555-5555-5555-555555555555", "EXIT", exit_time, exit_camera)]},
    )

    assert entry_response.status_code == 200
    assert exit_response.status_code == 200

    stored_exit_event = db_session.query(Event).filter_by(event_id="55555555-5555-5555-5555-555555555555").one()
    assert stored_exit_event.event_type == "EXIT"
    assert stored_exit_event.camera_id == exit_camera

    session = db_session.query(VisitorSession).filter_by(visitor_id="VIS_EXIT_001").one()
    assert session.session_end == exit_time.replace(tzinfo=None)

    metrics_response = client.get("/stores/STORE_BLR_001/metrics")
    funnel_response = client.get("/stores/STORE_BLR_001/funnel")

    assert metrics_response.status_code == 200
    assert funnel_response.status_code == 200

    metrics_payload = metrics_response.json()
    assert metrics_payload["active_visitors"] == 0
    assert metrics_payload["avg_session_duration_seconds"] == 900.0

    funnel_payload = funnel_response.json()["stages"]
    assert funnel_payload[0]["count"] == 1
    assert funnel_payload[3]["count"] == 0
