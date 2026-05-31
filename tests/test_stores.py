from datetime import datetime, timezone

from app.models.event import Event


def test_list_analytics_stores_orders_by_activity(client, db_session) -> None:
    """Dashboard store discovery should prefer stores that actually have data."""

    db_session.add_all(
        [
            Event(
                event_id="store-a-1",
                store_id="STORE_A",
                camera_id="CAM_01",
                visitor_id="VIS_001",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc),
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="store-b-1",
                store_id="STORE_B",
                camera_id="CAM_01",
                visitor_id="VIS_002",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 12, 1, tzinfo=timezone.utc),
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="store-b-2",
                store_id="STORE_B",
                camera_id="CAM_02",
                visitor_id="VIS_003",
                event_type="ZONE_ENTER",
                timestamp=datetime(2026, 3, 3, 12, 2, tzinfo=timezone.utc),
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/stores")

    assert response.status_code == 200
    assert response.json()["store_ids"] == ["STORE_B", "STORE_A"]
