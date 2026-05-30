import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.transaction import TransactionIngestRequest
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/ingest", status_code=status.HTTP_200_OK)
def ingest_transactions(
    payload: TransactionIngestRequest,
    db: Session = Depends(get_db),
) -> dict[str, int]:
    """Ingest a batch of transactions and update session conversion state."""

    try:
        return TransactionService().ingest_transactions(transactions=payload.transactions, db=db)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while ingesting transactions")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest transactions due to a database error.",
        )
    except Exception:
        db.rollback()
        logger.exception("Unexpected error while ingesting transactions")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while ingesting transactions.",
        )