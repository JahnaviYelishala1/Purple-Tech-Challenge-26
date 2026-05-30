import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.pipeline import StorePipelineStatusResponse
from app.services.pipeline_status_service import PipelineStatusService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stores", tags=["Pipeline Status"])


@router.get("/{store_id}/pipeline-status", response_model=StorePipelineStatusResponse)
def get_store_pipeline_status(store_id: str, db: Session = Depends(get_db)) -> StorePipelineStatusResponse:
    """Return the current CCTV pipeline status for a single store."""

    try:
        return PipelineStatusService().get_store_pipeline_status(store_id=store_id, db=db)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while loading store pipeline status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load store pipeline status due to a database error.",
        )
    except Exception:
        db.rollback()
        logger.exception("Unexpected error while loading store pipeline status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while loading store pipeline status.",
        )