from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.session import VisitorSession
from app.models.transaction import Transaction

DEMO_STORE_ID = "STORE_BLR_001"


def seed_demo_data_if_empty(db: Session) -> bool:
    """Seed a fresh database with stable dashboard demo data."""

    existing_sessions = db.execute(
        select(func.count()).where(VisitorSession.store_id == DEMO_STORE_ID)
    ).scalar_one()
    existing_events = db.execute(select(func.count()).where(Event.store_id == DEMO_STORE_ID)).scalar_one()
    if existing_sessions or existing_events:
        return False

    base_time = datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(minutes=45)
    visitors = [
        ("VIS_DEMO_001", True, 18),
        ("VIS_DEMO_002", True, 26),
        ("VIS_DEMO_003", False, 32),
        ("VIS_DEMO_004", False, 38),
        ("VIS_DEMO_005", False, 43),
        ("VIS_DEMO_006", False, 44),
        ("VIS_DEMO_007", False, 45),
    ]

    events: list[Event] = []
    sessions: list[VisitorSession] = []
    transactions: list[Transaction] = []

    for index, (visitor_id, converted, offset_minutes) in enumerate(visitors, start=1):
        entry_time = base_time + timedelta(minutes=offset_minutes)
        session_end = entry_time + timedelta(minutes=12 + index)
        sessions.append(
            VisitorSession(
                visitor_id=visitor_id,
                store_id=DEMO_STORE_ID,
                session_start=entry_time,
                session_end=session_end,
                converted=converted,
                is_staff=False,
            )
        )
        events.append(
            Event(
                event_id=f"demo-entry-{index}",
                store_id=DEMO_STORE_ID,
                camera_id="CAM2",
                visitor_id=visitor_id,
                event_type="ENTRY",
                timestamp=entry_time,
                dwell_ms=0,
                is_staff=False,
                confidence=0.96,
            )
        )

        if index <= 6:
            zone_id = "electronics" if index % 2 else "grocery"
            events.extend(
                [
                    Event(
                        event_id=f"demo-zone-enter-{index}",
                        store_id=DEMO_STORE_ID,
                        camera_id="CAM5",
                        visitor_id=visitor_id,
                        event_type="ZONE_ENTER",
                        timestamp=entry_time + timedelta(minutes=3),
                        zone_id=zone_id,
                        dwell_ms=0,
                        is_staff=False,
                        confidence=0.94,
                    ),
                    Event(
                        event_id=f"demo-zone-dwell-{index}",
                        store_id=DEMO_STORE_ID,
                        camera_id="CAM5",
                        visitor_id=visitor_id,
                        event_type="ZONE_DWELL",
                        timestamp=entry_time + timedelta(minutes=6),
                        zone_id=zone_id,
                        dwell_ms=25000 + (index * 3000),
                        is_staff=False,
                        confidence=0.94,
                    ),
                ]
            )

        if index >= 2:
            events.append(
                Event(
                    event_id=f"demo-billing-{index}",
                    store_id=DEMO_STORE_ID,
                    camera_id="CAM5",
                    visitor_id=visitor_id,
                    event_type="BILLING_QUEUE_JOIN",
                    timestamp=entry_time + timedelta(minutes=8),
                    dwell_ms=0,
                    is_staff=False,
                    confidence=0.95,
                    queue_depth=3 + index,
                )
            )

        if converted:
            transactions.append(
                Transaction(
                    transaction_id=f"demo-txn-{index}",
                    store_id=DEMO_STORE_ID,
                    timestamp=session_end,
                    basket_value=1200.0 + (index * 350.0),
                )
            )

    db.add_all([*sessions, *events, *transactions])
    db.commit()
    return True
