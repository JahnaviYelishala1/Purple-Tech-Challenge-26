from datetime import datetime, timezone

from app.models.event import Event


def test_heatmap_maps_legacy_demo_labels_to_dataset_safe_zones(client, db_session) -> None:
    """Dataset-aligned zone labels should be normalized before the dashboard renders them."""

    db_session.add_all(
        [
            Event(
                event_id="heatmap-legacy-1",
                store_id="STORE_BLR_001",
                camera_id="CAM1",
                visitor_id="VIS_001",
                event_type="ZONE_ENTER",
                timestamp=datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc),
                zone_id="makeup",
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="heatmap-legacy-2",
                store_id="STORE_BLR_001",
                camera_id="CAM3",
                visitor_id="VIS_002",
                event_type="ZONE_DWELL",
                timestamp=datetime(2026, 3, 3, 12, 5, tzinfo=timezone.utc),
                zone_id="bath-and-body",
                dwell_ms=42000,
                is_staff=False,
                confidence=0.95,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/stores/STORE_BLR_001/heatmap")

    assert response.status_code == 200
    zones = response.json()["zones"]
    assert {zone["zone_id"] for zone in zones} == {"Makeup", "Bath & Body"}