from datetime import datetime, timezone

from app.models.event import Event


def test_staff_events_are_excluded_from_funnel_and_heatmap(client, db_session) -> None:
    """Staff events should not affect customer funnel or zone analytics."""

    db_session.add_all(
        [
            Event(
                event_id="staff-entry-1",
                store_id="STORE_BLR_001",
                camera_id="CAM4",
                visitor_id="STAFF_001",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc),
                zone_id=None,
                dwell_ms=0,
                is_staff=True,
                confidence=0.95,
            ),
            Event(
                event_id="customer-entry-1",
                store_id="STORE_BLR_001",
                camera_id="CAM3",
                visitor_id="VIS_001",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 12, 5, tzinfo=timezone.utc),
                zone_id=None,
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="staff-zone-1",
                store_id="STORE_BLR_001",
                camera_id="CAM4",
                visitor_id="STAFF_001",
                event_type="ZONE_ENTER",
                timestamp=datetime(2026, 3, 3, 12, 10, tzinfo=timezone.utc),
                zone_id="staff-room",
                dwell_ms=0,
                is_staff=True,
                confidence=0.95,
            ),
            Event(
                event_id="customer-zone-1",
                store_id="STORE_BLR_001",
                camera_id="CAM2",
                visitor_id="VIS_001",
                event_type="ZONE_ENTER",
                timestamp=datetime(2026, 3, 3, 12, 12, tzinfo=timezone.utc),
                zone_id="skincare",
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
        ]
    )
    db_session.commit()

    funnel_response = client.get("/stores/STORE_BLR_001/funnel")
    heatmap_response = client.get("/stores/STORE_BLR_001/heatmap")

    assert funnel_response.status_code == 200
    assert funnel_response.json()["stages"][0]["count"] == 1
    assert funnel_response.json()["stages"][1]["count"] == 1

    assert heatmap_response.status_code == 200
    zones = heatmap_response.json()["zones"]
    assert len(zones) == 1
    assert zones[0]["zone_id"] == "SKINCARE"