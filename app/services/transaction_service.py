from collections.abc import Sequence
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.event import Event as EventModel
from app.models.session import VisitorSession
from app.models.transaction import Transaction as TransactionModel
from app.schemas.transaction import TransactionCreate


class TransactionService:
    """Service for ingesting transactions and updating conversion state."""

    def _find_correlated_session(
        self,
        db: Session,
        transaction: TransactionCreate,
        *,
        window: timedelta,
    ) -> VisitorSession | None:
        billing_window_start = transaction.timestamp - window

        session_statement = (
            select(VisitorSession)
            .where(
                VisitorSession.store_id == transaction.store_id,
                VisitorSession.is_staff.is_(False),
                VisitorSession.session_start <= transaction.timestamp,
            )
            .order_by(VisitorSession.session_start.desc())
        )

        for session in db.scalars(session_statement):
            billing_statement = select(func.count()).where(
                EventModel.store_id == transaction.store_id,
                EventModel.visitor_id == session.visitor_id,
                EventModel.event_type == "BILLING_QUEUE_JOIN",
                EventModel.is_staff.is_(False),
                EventModel.timestamp >= billing_window_start,
                EventModel.timestamp <= transaction.timestamp,
                EventModel.timestamp >= session.session_start,
            )
            if int(db.execute(billing_statement).scalar_one() or 0) > 0:
                return session

        return None

    def ingest_transactions(
        self,
        transactions: Sequence[TransactionCreate],
        db: Session,
    ) -> dict[str, int]:
        """Insert non-duplicate transactions and mark related sessions as converted."""

        total_received = len(transactions)
        if total_received == 0:
            return {
                "total_received": 0,
                "inserted": 0,
                "duplicates": 0,
                "sessions_converted": 0,
            }

        incoming_ids = [transaction.transaction_id for transaction in transactions]
        existing_ids = set(
            db.scalars(
                select(TransactionModel.transaction_id).where(
                    TransactionModel.transaction_id.in_(incoming_ids)
                )
            ).all()
        )

        seen_ids = set(existing_ids)
        rows_to_insert: list[TransactionModel] = []
        duplicates = 0
        sessions_converted = 0
        conversion_window = timedelta(minutes=get_settings().pos_conversion_window_minutes)

        for transaction in transactions:
            transaction_id = transaction.transaction_id
            if transaction_id in seen_ids:
                duplicates += 1
                continue

            seen_ids.add(transaction_id)
            rows_to_insert.append(
                TransactionModel(
                    transaction_id=transaction_id,
                    store_id=transaction.store_id,
                    timestamp=transaction.timestamp,
                    basket_value=transaction.basket_value,
                )
            )

            correlated_session = self._find_correlated_session(db, transaction, window=conversion_window)
            if correlated_session is not None and not correlated_session.converted:
                correlated_session.converted = True
                sessions_converted += 1

        if rows_to_insert:
            db.add_all(rows_to_insert)

        db.commit()

        return {
            "total_received": total_received,
            "inserted": len(rows_to_insert),
            "duplicates": duplicates,
            "sessions_converted": sessions_converted,
        }