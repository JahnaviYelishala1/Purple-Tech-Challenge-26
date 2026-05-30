from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.store import StoreCreate, StoreRead
from app.services.store_service import StoreService

router = APIRouter(prefix="/stores", tags=["stores"])


@router.get("", response_model=list[StoreRead])
def list_stores(db: Session = Depends(get_db)) -> list[StoreRead]:
    return StoreService(db).list_stores()


@router.post("", response_model=StoreRead, status_code=status.HTTP_201_CREATED)
def create_store(payload: StoreCreate, db: Session = Depends(get_db)) -> StoreRead:
    return StoreService(db).create_store(payload)