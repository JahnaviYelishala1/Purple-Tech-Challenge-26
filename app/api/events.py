import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.ingestion import EventIngestRequest
from app.services.event_ingestion import EventIngestionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/ingest", status_code=status.HTTP_200_OK)
def ingest_events(payload: EventIngestRequest, db: Session = Depends(get_db)) -> dict[str, int]:
    """Ingest a batch of events and return insertion statistics."""

    try:
        service = EventIngestionService()
        return service.ingest_events(events=payload.events, db=db)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while ingesting events")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest events due to a database error.",
        )
    except Exception:
        db.rollback()
        logger.exception("Unexpected error while ingesting events")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while ingesting events.",
        )