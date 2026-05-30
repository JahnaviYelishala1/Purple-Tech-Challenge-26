import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.funnel import StoreFunnelResponse
from app.services.funnel_service import FunnelService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stores", tags=["Funnel"])


@router.get("/{store_id}/funnel", response_model=StoreFunnelResponse)
def get_store_funnel(store_id: str, db: Session = Depends(get_db)) -> StoreFunnelResponse:
    """Return funnel analytics for a single store."""

    try:
        funnel = FunnelService().get_store_funnel(store_id=store_id, db=db)
        return StoreFunnelResponse.model_validate(funnel)
    except SQLAlchemyError:
        logger.exception("Database error while loading store funnel")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load store funnel due to a database error.",
        )
    except Exception:
        logger.exception("Unexpected error while loading store funnel")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while loading store funnel.",
        )