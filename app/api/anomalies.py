import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.anomaly import StoreAnomaliesResponse
from app.services.anomaly_service import AnomalyService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stores", tags=["Anomalies"])


@router.get("/{store_id}/anomalies", response_model=StoreAnomaliesResponse)
def get_store_anomalies(store_id: str, db: Session = Depends(get_db)) -> StoreAnomaliesResponse:
    """Return detected operational anomalies for a single store."""

    try:
        return AnomalyService().get_store_anomalies(store_id=store_id, db=db)
    except SQLAlchemyError:
        logger.exception("Database error while loading store anomalies")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load store anomalies due to a database error.",
        )
    except Exception:
        logger.exception("Unexpected error while loading store anomalies")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while loading store anomalies.",
        )