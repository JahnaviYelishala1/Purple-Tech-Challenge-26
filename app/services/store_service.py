from sqlalchemy.orm import Session

from app.models.store import Store
from app.schemas.store import StoreCreate


class StoreService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_stores(self) -> list[Store]:
        return self.db.query(Store).order_by(Store.name).all()

    def create_store(self, payload: StoreCreate) -> Store:
        store = Store(name=payload.name, region=payload.region)
        self.db.add(store)
        self.db.commit()
        self.db.refresh(store)
        return store