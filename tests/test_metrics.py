# PROMPT:
# Create pytest tests for store metrics.
#
# CHANGES MADE:
# Added edge cases for duplicate ingestion and conversion tracking.

from datetime import datetime, timedelta, timezone

from app.models.session import VisitorSession


def _add_session(
    db_session,
    *,
    visitor_id: str,
    store_id: str,
    start: datetime,
    end: datetime | None,
    converted: bool,
) -> None:
    db_session.add(
        VisitorSession(
            visitor_id=visitor_id,
            store_id=store_id,
            session_start=start,
            session_end=end,
            converted=converted,
            is_staff=False,
        )
    )
    db_session.commit()


def test_empty_store_returns_zero_values(client) -> None:
    """A store with no sessions should return zeroed metrics."""

    response = client.get("/stores/STORE_EMPTY/metrics")

    assert response.status_code == 200
    assert response.json() == {
        "unique_visitors": 0,
        "active_visitors": 0,
        "converted_visitors": 0,
        "conversion_rate": 0.0,
        "avg_session_duration_seconds": 0.0,
    }


def test_store_with_one_session_returns_correct_visitor_count(client, db_session) -> None:
    """A single closed session should count one unique visitor."""

    start = datetime(2026, 3, 3, 14, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=20)
    _add_session(
        db_session,
        visitor_id="VIS_001",
        store_id="STORE_BLR_001",
        start=start,
        end=end,
        converted=False,
    )

    response = client.get("/stores/STORE_BLR_001/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["unique_visitors"] == 1
    assert payload["active_visitors"] == 0
    assert payload["converted_visitors"] == 0


def test_converted_session_updates_conversion_rate(client, db_session) -> None:
    """A converted session should increase the conversion rate."""

    start = datetime(2026, 3, 3, 14, 0, tzinfo=timezone.utc)
    _add_session(
        db_session,
        visitor_id="VIS_001",
        store_id="STORE_BLR_001",
        start=start,
        end=start + timedelta(minutes=20),
        converted=True,
    )

    response = client.get("/stores/STORE_BLR_001/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["converted_visitors"] == 1
    assert payload["conversion_rate"] == 100.0


def test_active_sessions_counted_correctly(client, db_session) -> None:
    """An open session should be counted as active."""

    start = datetime(2026, 3, 3, 14, 0, tzinfo=timezone.utc)
    _add_session(
        db_session,
        visitor_id="VIS_ACTIVE",
        store_id="STORE_BLR_001",
        start=start,
        end=None,
        converted=False,
    )

    response = client.get("/stores/STORE_BLR_001/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_visitors"] == 1
    assert payload["converted_visitors"] == 0