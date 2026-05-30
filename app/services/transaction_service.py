from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.session import VisitorSession
from app.models.transaction import Transaction as TransactionModel
from app.schemas.transaction import TransactionCreate


class TransactionService:
    """Service for ingesting transactions and updating conversion state."""

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

            statement = (
                select(VisitorSession)
                .where(VisitorSession.store_id == transaction.store_id)
                .order_by(VisitorSession.session_start.desc())
            )
            most_recent_session = db.scalars(statement).first()
            if most_recent_session is not None and not most_recent_session.converted:
                most_recent_session.converted = True
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