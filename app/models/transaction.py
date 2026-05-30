from datetime import datetime

from sqlalchemy import DateTime, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Transaction(Base):
    """SQLAlchemy model for retail basket transactions."""

    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_store_timestamp", "store_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    store_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    basket_value: Mapped[float] = mapped_column(Float, nullable=False)

    def __repr__(self) -> str:
        """Return a concise debugging representation."""

        return (
            f"Transaction(id={self.id!r}, transaction_id={self.transaction_id!r}, "
            f"store_id={self.store_id!r}, timestamp={self.timestamp!r}, basket_value={self.basket_value!r})"
        )