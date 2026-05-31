from datetime import datetime, timezone

from app.models.event import Event
from app.models.session import VisitorSession


def _seed_session(db_session, *, visitor_id: str, start: datetime, converted: bool = False) -> None:
    db_session.add(
        VisitorSession(
            visitor_id=visitor_id,
            store_id="STORE_BLR_001",
            session_start=start,
            session_end=None,
            converted=converted,
            is_staff=False,
        )
    )
    db_session.commit()


def _transaction_payload(transaction_id: str, timestamp: str) -> dict[str, object]:
    return {
        "transactions": [
            {
                "transaction_id": transaction_id,
                "store_id": "STORE_BLR_001",
                "timestamp": timestamp,
                "basket_value": 1250.0,
            }
        ]
    }


def test_transaction_converts_session_when_billing_event_exists(client, db_session) -> None:
    """A POS transaction should convert the matching session when billing activity exists within the window."""

    start_time = datetime(2026, 3, 3, 14, 0, tzinfo=timezone.utc)
    billing_time = datetime(2026, 3, 3, 14, 10, tzinfo=timezone.utc)
    transaction_time = datetime(2026, 3, 3, 14, 20, tzinfo=timezone.utc)

    _seed_session(db_session, visitor_id="VIS_001", start=start_time)
    db_session.add(
        Event(
            event_id="txn-corr-billing",
            store_id="STORE_BLR_001",
            camera_id="CAM5",
            visitor_id="VIS_001",
            event_type="BILLING_QUEUE_JOIN",
            timestamp=billing_time,
            zone_id="billing",
            dwell_ms=0,
            is_staff=False,
            confidence=0.95,
        )
    )
    db_session.commit()

    response = client.post(
        "/transactions/ingest",
        json=_transaction_payload("txn-001", transaction_time.isoformat()),
    )

    assert response.status_code == 200
    assert response.json()["sessions_converted"] == 1
    updated_session = db_session.query(VisitorSession).filter_by(visitor_id="VIS_001").one()
    assert updated_session.converted is True


def test_transaction_without_billing_event_does_not_convert(client, db_session) -> None:
    """A POS transaction without billing activity should not convert the session."""

    start_time = datetime(2026, 3, 3, 15, 0, tzinfo=timezone.utc)
    transaction_time = datetime(2026, 3, 3, 15, 10, tzinfo=timezone.utc)

    _seed_session(db_session, visitor_id="VIS_002", start=start_time)

    response = client.post(
        "/transactions/ingest",
        json=_transaction_payload("txn-002", transaction_time.isoformat()),
    )

    assert response.status_code == 200
    assert response.json()["sessions_converted"] == 0
    updated_session = db_session.query(VisitorSession).filter_by(visitor_id="VIS_002").one()
    assert updated_session.converted is False