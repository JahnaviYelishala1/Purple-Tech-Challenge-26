from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.event import Event
from app.models.session import VisitorSession
from app.models.transaction import Transaction

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.get("")
def list_analytics_stores(db: Session = Depends(get_db)) -> dict[str, list[str]]:
    """Return store IDs that have analytics data available for the dashboard."""

    activity_by_store: dict[str, int] = {}
    statements = (
        select(Event.store_id, func.count()).group_by(Event.store_id),
        select(VisitorSession.store_id, func.count()).group_by(VisitorSession.store_id),
        select(Transaction.store_id, func.count()).group_by(Transaction.store_id),
    )

    for statement in statements:
        for store_id, count in db.execute(statement).all():
            activity_by_store[str(store_id)] = activity_by_store.get(str(store_id), 0) + int(count or 0)

    store_ids = [
        store_id
        for store_id, _count in sorted(activity_by_store.items(), key=lambda item: (-item[1], item[0]))
    ]
    return {"store_ids": store_ids, "data": store_ids}
