# PROMPT:
# Create pytest tests for funnel analytics.
#
# CHANGES MADE:
# Added edge cases for duplicate ingestion and conversion tracking.

from datetime import datetime, timezone

from app.models.event import Event
from app.models.session import VisitorSession


def _seed_funnel_data(db_session) -> None:
    db_session.add_all(
        [
            Event(
                event_id="funnel-1",
                store_id="STORE_BLR_001",
                camera_id="CAM_01",
                visitor_id="VIS_A",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 13, 0, tzinfo=timezone.utc),
                zone_id=None,
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="funnel-2",
                store_id="STORE_BLR_001",
                camera_id="CAM_01",
                visitor_id="VIS_B",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 13, 1, tzinfo=timezone.utc),
                zone_id=None,
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="funnel-3",
                store_id="STORE_BLR_001",
                camera_id="CAM_02",
                visitor_id="VIS_A",
                event_type="ZONE_ENTER",
                timestamp=datetime(2026, 3, 3, 13, 5, tzinfo=timezone.utc),
                zone_id="SKINCARE",
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="funnel-4",
                store_id="STORE_BLR_001",
                camera_id="CAM_03",
                visitor_id="VIS_B",
                event_type="BILLING_QUEUE_JOIN",
                timestamp=datetime(2026, 3, 3, 13, 10, tzinfo=timezone.utc),
                zone_id="BILLING",
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
        ]
    )
    db_session.add(
        VisitorSession(
            visitor_id="VIS_A",
            store_id="STORE_BLR_001",
            session_start=datetime(2026, 3, 3, 13, 0, tzinfo=timezone.utc),
            session_end=datetime(2026, 3, 3, 13, 20, tzinfo=timezone.utc),
            converted=True,
            is_staff=False,
        )
    )
    db_session.commit()


def test_empty_funnel_returns_zeroed_stage_counts(client) -> None:
    """An empty store should return a zeroed funnel structure."""

    response = client.get("/stores/STORE_EMPTY/funnel")

    assert response.status_code == 200
    payload = response.json()
    assert payload["stages"] == [
        {"stage": "ENTRY", "count": 0, "dropoff_percentage": 0.0},
        {"stage": "ZONE_VISIT", "count": 0, "dropoff_percentage": 0.0},
        {"stage": "BILLING_QUEUE", "count": 0, "dropoff_percentage": 0.0},
        {"stage": "PURCHASE", "count": 0, "dropoff_percentage": 0.0},
    ]


def test_entry_stage_counts_correctly(client, db_session) -> None:
    """Entry stage should count unique visitors with ENTRY events."""

    db_session.add_all(
        [
            Event(
                event_id="entry-1",
                store_id="STORE_BLR_001",
                camera_id="CAM_01",
                visitor_id="VIS_A",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 13, 0, tzinfo=timezone.utc),
                zone_id=None,
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="entry-2",
                store_id="STORE_BLR_001",
                camera_id="CAM_01",
                visitor_id="VIS_B",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 13, 1, tzinfo=timezone.utc),
                zone_id=None,
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="entry-3",
                store_id="STORE_BLR_001",
                camera_id="CAM_01",
                visitor_id="VIS_A",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 13, 2, tzinfo=timezone.utc),
                zone_id=None,
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/stores/STORE_BLR_001/funnel")

    assert response.status_code == 200
    assert response.json()["stages"][0]["count"] == 2


def test_zone_visit_stage_counts_correctly(client, db_session) -> None:
    """Zone visit stage should count unique visitors with zone enter or dwell events."""

    db_session.add_all(
        [
            Event(
                event_id="zone-1",
                store_id="STORE_BLR_001",
                camera_id="CAM_02",
                visitor_id="VIS_A",
                event_type="ZONE_ENTER",
                timestamp=datetime(2026, 3, 3, 13, 5, tzinfo=timezone.utc),
                zone_id="SKINCARE",
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="zone-2",
                store_id="STORE_BLR_001",
                camera_id="CAM_02",
                visitor_id="VIS_B",
                event_type="ZONE_DWELL",
                timestamp=datetime(2026, 3, 3, 13, 6, tzinfo=timezone.utc),
                zone_id="MAKEUP",
                dwell_ms=20000,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="zone-3",
                store_id="STORE_BLR_001",
                camera_id="CAM_02",
                visitor_id="VIS_A",
                event_type="ZONE_DWELL",
                timestamp=datetime(2026, 3, 3, 13, 7, tzinfo=timezone.utc),
                zone_id="SKINCARE",
                dwell_ms=45000,
                is_staff=False,
                confidence=0.95,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/stores/STORE_BLR_001/funnel")

    assert response.status_code == 200
    assert response.json()["stages"][1]["count"] == 2


def test_purchase_stage_counts_correctly(client, db_session) -> None:
    """Purchase stage should count converted sessions."""

    db_session.add(
        VisitorSession(
            visitor_id="VIS_A",
            store_id="STORE_BLR_001",
            session_start=datetime(2026, 3, 3, 13, 0, tzinfo=timezone.utc),
            session_end=datetime(2026, 3, 3, 13, 20, tzinfo=timezone.utc),
            converted=True,
            is_staff=False,
        )
    )
    db_session.commit()

    response = client.get("/stores/STORE_BLR_001/funnel")

    assert response.status_code == 200
    assert response.json()["stages"][3]["count"] == 1


def test_store_funnel_returns_stage_counts(client, db_session) -> None:
    """The funnel endpoint should return the expected ordered stage structure."""

    _seed_funnel_data(db_session)

    response = client.get("/stores/STORE_BLR_001/funnel")

    assert response.status_code == 200
    payload = response.json()
    assert [stage["stage"] for stage in payload["stages"]] == [
        "ENTRY",
        "ZONE_VISIT",
        "BILLING_QUEUE",
        "PURCHASE",
    ]
    assert payload["stages"][0]["count"] == 2
    assert payload["stages"][1]["count"] == 1
    assert payload["stages"][2]["count"] == 1
    assert payload["stages"][3]["count"] == 1


def test_dropoff_percentages_are_calculated_correctly(client, db_session) -> None:
    """Dropoff percentages should reflect the step-to-step funnel decline."""

    entry_visitors = [f"VIS_E_{index}" for index in range(10)]
    zone_visitors = entry_visitors[:8]
    billing_visitors = entry_visitors[:5]
    converted_visitors = entry_visitors[:3]

    db_session.add_all(
        [
            Event(
                event_id=f"drop-entry-{index}",
                store_id="STORE_BLR_001",
                camera_id="CAM_01",
                visitor_id=visitor_id,
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 13, index, tzinfo=timezone.utc),
                zone_id=None,
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            )
            for index, visitor_id in enumerate(entry_visitors)
        ]
        + [
            Event(
                event_id=f"drop-zone-{index}",
                store_id="STORE_BLR_001",
                camera_id="CAM_02",
                visitor_id=visitor_id,
                event_type="ZONE_ENTER",
                timestamp=datetime(2026, 3, 3, 14, index, tzinfo=timezone.utc),
                zone_id="SKINCARE",
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            )
            for index, visitor_id in enumerate(zone_visitors)
        ]
        + [
            Event(
                event_id=f"drop-billing-{index}",
                store_id="STORE_BLR_001",
                camera_id="CAM_03",
                visitor_id=visitor_id,
                event_type="BILLING_QUEUE_JOIN",
                timestamp=datetime(2026, 3, 3, 15, index, tzinfo=timezone.utc),
                zone_id="BILLING",
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            )
            for index, visitor_id in enumerate(billing_visitors)
        ]
    )
    db_session.add_all(
        [
            VisitorSession(
                visitor_id=visitor_id,
                store_id="STORE_BLR_001",
                session_start=datetime(2026, 3, 3, 16, index, tzinfo=timezone.utc),
                session_end=datetime(2026, 3, 3, 16, index, tzinfo=timezone.utc),
                converted=True,
                is_staff=False,
            )
            for index, visitor_id in enumerate(converted_visitors)
        ]
    )
    db_session.commit()

    response = client.get("/stores/STORE_BLR_001/funnel")

    assert response.status_code == 200
    payload = response.json()["stages"]
    assert payload[0]["dropoff_percentage"] == 0.0
    assert payload[1]["dropoff_percentage"] == 20.0
    assert payload[2]["dropoff_percentage"] == 37.5
    assert payload[3]["dropoff_percentage"] == 40.0


def test_funnel_counts_never_increase(client, db_session) -> None:
    """Stage counts should be clamped so later stages never exceed earlier ones."""

    db_session.add_all(
        [
            Event(
                event_id="monotonic-entry-1",
                store_id="STORE_BLR_001",
                camera_id="CAM_01",
                visitor_id="VIS_1",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 13, 0, tzinfo=timezone.utc),
                zone_id=None,
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="monotonic-entry-2",
                store_id="STORE_BLR_001",
                camera_id="CAM_01",
                visitor_id="VIS_2",
                event_type="ENTRY",
                timestamp=datetime(2026, 3, 3, 13, 1, tzinfo=timezone.utc),
                zone_id=None,
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="monotonic-zone-1",
                store_id="STORE_BLR_001",
                camera_id="CAM_02",
                visitor_id="VIS_1",
                event_type="ZONE_ENTER",
                timestamp=datetime(2026, 3, 3, 13, 2, tzinfo=timezone.utc),
                zone_id="SKINCARE",
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="monotonic-zone-2",
                store_id="STORE_BLR_001",
                camera_id="CAM_02",
                visitor_id="VIS_2",
                event_type="ZONE_ENTER",
                timestamp=datetime(2026, 3, 3, 13, 3, tzinfo=timezone.utc),
                zone_id="SKINCARE",
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="monotonic-zone-3",
                store_id="STORE_BLR_001",
                camera_id="CAM_02",
                visitor_id="VIS_3",
                event_type="ZONE_ENTER",
                timestamp=datetime(2026, 3, 3, 13, 4, tzinfo=timezone.utc),
                zone_id="SKINCARE",
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
            Event(
                event_id="monotonic-zone-4",
                store_id="STORE_BLR_001",
                camera_id="CAM_02",
                visitor_id="VIS_4",
                event_type="ZONE_ENTER",
                timestamp=datetime(2026, 3, 3, 13, 5, tzinfo=timezone.utc),
                zone_id="SKINCARE",
                dwell_ms=0,
                is_staff=False,
                confidence=0.95,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/stores/STORE_BLR_001/funnel")

    assert response.status_code == 200
    counts = [stage["count"] for stage in response.json()["stages"]]
    assert counts == sorted(counts, reverse=True)
    assert counts[0] == 2
    assert counts[1] == 2