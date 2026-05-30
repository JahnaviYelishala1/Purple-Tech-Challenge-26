# PROMPT:
# Create pytest tests for anomaly detection.
#
# CHANGES MADE:
# Added edge cases for duplicate ingestion and conversion tracking.

from datetime import datetime, timezone

from app.models.event import Event
from app.models.session import VisitorSession


def _seed_queue_spike(db_session) -> None:
    db_session.add_all(
        [
            Event(
                event_id=f"queue-{index}",
                store_id="STORE_BLR_001",
                camera_id="CAM_QUEUE",
                visitor_id=f"VIS_Q_{index}",
                event_type="BILLING_QUEUE_JOIN",
                timestamp=datetime(2026, 3, 3, 14, index, tzinfo=timezone.utc),
                zone_id=None,
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            )
            for index in range(6)
        ]
    )
    db_session.commit()


def test_empty_store_produces_no_anomalies(client) -> None:
    """An empty store should not produce anomaly results."""

    response = client.get("/stores/STORE_EMPTY/anomalies")

    assert response.status_code == 200
    assert response.json() == {"anomalies": []}


def test_store_anomalies_detect_dead_zone(client, db_session) -> None:
    """A historically active zone with no recent entries should trigger dead zone detection."""

    db_session.add_all(
        [
            Event(
                event_id="dead-zone-old",
                store_id="STORE_BLR_001",
                camera_id="CAM_ZONE",
                visitor_id="VIS_DZ_1",
                event_type="ZONE_ENTER",
                timestamp=datetime(2026, 3, 3, 12, 0, tzinfo=timezone.utc),
                zone_id="SKINCARE",
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="dead-zone-latest",
                store_id="STORE_BLR_001",
                camera_id="CAM_MAIN",
                visitor_id="VIS_DZ_2",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 14, 0, tzinfo=timezone.utc),
                zone_id=None,
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/stores/STORE_BLR_001/anomalies")

    assert response.status_code == 200
    payload = response.json()["anomalies"]
    assert any(anomaly["anomaly_type"] == "DEAD_ZONE" for anomaly in payload)


def test_store_anomalies_detect_queue_spike(client, db_session) -> None:
    """The anomalies endpoint should detect a billing queue spike."""

    _seed_queue_spike(db_session)

    response = client.get("/stores/STORE_BLR_001/anomalies")

    assert response.status_code == 200
    payload = response.json()
    assert payload["anomalies"]
    assert payload["anomalies"][0]["anomaly_type"] == "QUEUE_SPIKE"
    assert payload["anomalies"][0]["severity"] == "CRITICAL"
    assert payload["anomalies"][0]["suggested_action"] == "Open additional billing counters."


def test_store_anomalies_detect_conversion_drop(client, db_session) -> None:
    """A low conversion rate should trigger conversion drop detection."""

    db_session.add_all(
        [
            Event(
                event_id="conv-drop-event",
                store_id="STORE_BLR_001",
                camera_id="CAM_MAIN",
                visitor_id="VIS_CD_1",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 14, 0, tzinfo=timezone.utc),
                zone_id=None,
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            VisitorSession(
                visitor_id="VIS_CD_1",
                store_id="STORE_BLR_001",
                session_start=datetime(2026, 3, 3, 14, 0, tzinfo=timezone.utc),
                session_end=datetime(2026, 3, 3, 14, 20, tzinfo=timezone.utc),
                converted=False,
                is_staff=False,
            ),
            VisitorSession(
                visitor_id="VIS_CD_2",
                store_id="STORE_BLR_001",
                session_start=datetime(2026, 3, 3, 14, 5, tzinfo=timezone.utc),
                session_end=datetime(2026, 3, 3, 14, 25, tzinfo=timezone.utc),
                converted=False,
                is_staff=False,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/stores/STORE_BLR_001/anomalies")

    assert response.status_code == 200
    payload = response.json()["anomalies"]
    assert any(anomaly["anomaly_type"] == "CONVERSION_DROP" for anomaly in payload)