import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.metrics import StoreMetricsResponse
from app.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stores", tags=["Metrics"])


@router.get("/{store_id}/metrics", response_model=StoreMetricsResponse)
def get_store_metrics(store_id: str, db: Session = Depends(get_db)) -> StoreMetricsResponse:
    """Return funnel and conversion metrics for a single store."""

    try:
        metrics = MetricsService().get_store_metrics(store_id=store_id, db=db)
        return StoreMetricsResponse.model_validate(metrics)
    except SQLAlchemyError:
        logger.exception("Database error while loading store metrics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load store metrics due to a database error.",
        )
    except Exception:
        logger.exception("Unexpected error while loading store metrics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while loading store metrics.",
        )