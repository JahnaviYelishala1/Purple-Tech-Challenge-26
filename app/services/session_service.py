from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.session import VisitorSession
from app.schemas.event import Event


class SessionService:
    """Service for creating and updating visitor sessions."""

    def get_active_session(
        self,
        visitor_id: str,
        store_id: str,
        db: Session,
    ) -> VisitorSession | None:
        """Return the active session for a visitor and store, if one exists."""

        statement = (
            select(VisitorSession)
            .where(
                VisitorSession.visitor_id == visitor_id,
                VisitorSession.store_id == store_id,
                VisitorSession.session_end.is_(None),
            )
            .order_by(VisitorSession.session_start.desc())
        )
        return db.scalars(statement).first()

    def handle_entry_event(self, event: Event, db: Session) -> VisitorSession | None:
        """Create an active session for an entry event when needed."""

        if event.is_staff:
            return None

        active_session = self.get_active_session(event.visitor_id, event.store_id, db)
        if active_session is not None:
            return active_session

        session = VisitorSession(
            visitor_id=event.visitor_id,
            store_id=event.store_id,
            session_start=event.timestamp,
            converted=False,
            is_staff=event.is_staff,
        )
        db.add(session)
        db.flush()
        return session

    def handle_exit_event(self, event: Event, db: Session) -> VisitorSession | None:
        """Close the active session for an exit event, if one exists."""

        if event.is_staff:
            return None

        active_session = self.get_active_session(event.visitor_id, event.store_id, db)
        if active_session is None:
            return None

        active_session.session_end = event.timestamp
        db.flush()
        return active_session