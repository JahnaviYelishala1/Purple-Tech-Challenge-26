from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class VisitorSession(Base):
    """SQLAlchemy model for visitor sessions used in funnel analytics."""

    __tablename__ = "visitor_sessions"
    __table_args__ = (
        Index("ix_visitor_sessions_visitor_store_start", "visitor_id", "store_id", "session_start"),
        Index("ix_visitor_sessions_store_converted_start", "store_id", "converted", "session_start"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    visitor_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    store_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    session_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    session_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    converted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        """Return a concise debugging representation."""

        return (
            f"VisitorSession(id={self.id!r}, visitor_id={self.visitor_id!r}, store_id={self.store_id!r}, "
            f"session_start={self.session_start!r}, converted={self.converted!r})"
        )