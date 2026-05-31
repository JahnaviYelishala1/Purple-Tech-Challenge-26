from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.session import VisitorSession
from app.schemas.event import Event


class SessionService:
    """Service for creating and updating visitor sessions."""

    @staticmethod
    def _normalize_timestamp(timestamp: datetime) -> datetime:
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)

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

    def get_recent_closed_session(
        self,
        visitor_id: str,
        store_id: str,
        event_timestamp: datetime,
        db: Session,
        *,
        window_minutes: int | None = None,
    ) -> VisitorSession | None:
        """Return the most recent closed session within the configured re-entry window."""

        settings = get_settings()
        effective_window = settings.reentry_window_minutes if window_minutes is None else window_minutes
        if effective_window <= 0:
            return None

        normalized_timestamp = self._normalize_timestamp(event_timestamp)
        cutoff = normalized_timestamp - timedelta(minutes=effective_window)

        statement = (
            select(VisitorSession)
            .where(
                VisitorSession.visitor_id == visitor_id,
                VisitorSession.store_id == store_id,
                VisitorSession.session_end.is_not(None),
                VisitorSession.session_end >= cutoff,
                VisitorSession.session_end <= normalized_timestamp,
            )
            .order_by(VisitorSession.session_end.desc())
        )
        return db.scalars(statement).first()

    def is_recent_reentry(self, event: Event, db: Session) -> bool:
        """Return True when the event falls within the configured re-entry window."""

        return self.get_recent_closed_session(event.visitor_id, event.store_id, event.timestamp, db) is not None

    def _open_session(self, event: Event, db: Session) -> VisitorSession:
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

    def handle_entry_event(self, event: Event, db: Session) -> VisitorSession | None:
        """Create an active session for an entry event when needed."""

        if event.is_staff:
            return None

        active_session = self.get_active_session(event.visitor_id, event.store_id, db)
        if active_session is not None:
            return active_session

        return self._open_session(event, db)

    def handle_reentry_event(self, event: Event, db: Session) -> VisitorSession | None:
        """Create a new session for a returning visitor."""

        if event.is_staff:
            return None

        active_session = self.get_active_session(event.visitor_id, event.store_id, db)
        if active_session is not None:
            return active_session

        return self._open_session(event, db)

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