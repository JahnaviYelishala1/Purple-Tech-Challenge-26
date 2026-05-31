from app.db.demo_seed import DEMO_STORE_ID, seed_demo_data_if_empty
from app.models.event import Event
from app.models.session import VisitorSession
from app.models.transaction import Transaction


def test_seed_demo_data_populates_empty_database(db_session) -> None:
    seeded = seed_demo_data_if_empty(db_session)

    assert seeded is True
    assert db_session.query(VisitorSession).filter_by(store_id=DEMO_STORE_ID).count() == 7
    assert db_session.query(Event).filter_by(store_id=DEMO_STORE_ID, event_type="ENTRY").count() == 7
    assert db_session.query(Event).filter_by(store_id=DEMO_STORE_ID, event_type="BILLING_QUEUE_JOIN").count() == 6
    assert db_session.query(Transaction).filter_by(store_id=DEMO_STORE_ID).count() == 2


def test_seed_demo_data_is_idempotent(db_session) -> None:
    assert seed_demo_data_if_empty(db_session) is True
    assert seed_demo_data_if_empty(db_session) is False

    assert db_session.query(VisitorSession).filter_by(store_id=DEMO_STORE_ID).count() == 7
