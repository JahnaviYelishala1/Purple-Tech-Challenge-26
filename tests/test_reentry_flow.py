from datetime import datetime, timezone

from app.models.event import Event
from app.models.session import VisitorSession
from pipeline.camera_roles import camera_ids_for_role


def _payload(event_id: str, event_type: str, timestamp: datetime, visitor_id: str = "VIS_001") -> dict[str, object]:
    return {
        "event_id": event_id,
        "store_id": "STORE_BLR_001",
        "camera_id": camera_ids_for_role("ENTRANCE")[0],
        "visitor_id": visitor_id,
        "event_type": event_type,
        "timestamp": timestamp.isoformat(),
        "zone_id": "entrance",
        "dwell_ms": 0,
        "is_staff": False,
        "confidence": 0.95,
        "metadata": {},
    }


def test_entry_exit_reentry_flow(client, db_session) -> None:
    """A returning visitor within the reentry window should be stored as REENTRY."""

    entrance_camera = camera_ids_for_role("ENTRANCE")[0]
    exit_camera = camera_ids_for_role("EXIT")[0]

    entry_time = datetime(2026, 3, 3, 13, 0, tzinfo=timezone.utc)
    exit_time = datetime(2026, 3, 3, 13, 10, tzinfo=timezone.utc)
    reentry_time = datetime(2026, 3, 3, 13, 20, tzinfo=timezone.utc)

    entry_response = client.post(
        "/events/ingest",
        json={"events": [_payload("11111111-1111-1111-1111-111111111111", "ENTRY", entry_time)]},
    )
    exit_response = client.post(
        "/events/ingest",
        json={
            "events": [
                {
                    **_payload("22222222-2222-2222-2222-222222222222", "EXIT", exit_time),
                    "camera_id": exit_camera,
                    "zone_id": "exit",
                }
            ]
        },
    )
    reentry_response = client.post(
        "/events/ingest",
        json={
            "events": [
                {
                    **_payload("33333333-3333-3333-3333-333333333333", "ENTRY", reentry_time),
                    "camera_id": entrance_camera,
                }
            ]
        },
    )

    assert entry_response.status_code == 200
    assert exit_response.status_code == 200
    assert reentry_response.status_code == 200

    stored_events = (
        db_session.query(Event)
        .filter_by(store_id="STORE_BLR_001", visitor_id="VIS_001")
        .order_by(Event.timestamp.asc())
        .all()
    )
    assert [event.event_type for event in stored_events] == ["ENTRY", "EXIT", "REENTRY"]

    sessions = (
        db_session.query(VisitorSession)
        .filter_by(store_id="STORE_BLR_001", visitor_id="VIS_001")
        .order_by(VisitorSession.session_start.asc())
        .all()
    )
    assert len(sessions) == 2
    assert sessions[0].session_end == exit_time.replace(tzinfo=None)
    assert sessions[1].session_start == reentry_time.replace(tzinfo=None)
    assert sessions[1].session_end is None
