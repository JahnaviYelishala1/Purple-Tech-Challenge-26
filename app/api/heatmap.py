import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.heatmap import StoreHeatmapResponse
from app.services.heatmap_service import HeatmapService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stores", tags=["Heatmap"])


@router.get("/{store_id}/heatmap", response_model=StoreHeatmapResponse)
def get_store_heatmap(store_id: str, db: Session = Depends(get_db)) -> StoreHeatmapResponse:
    """Return zone-level heatmap analytics for a single store."""

    try:
        return HeatmapService().get_store_heatmap(store_id=store_id, db=db)
    except SQLAlchemyError:
        logger.exception("Database error while loading store heatmap")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load store heatmap due to a database error.",
        )
    except Exception:
        logger.exception("Unexpected error while loading store heatmap")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while loading store heatmap.",
        )