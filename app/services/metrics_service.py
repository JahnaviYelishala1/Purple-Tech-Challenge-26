from datetime import timezone

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.session import VisitorSession


class MetricsService:
    """Service for computing store-level visitor session metrics."""

    def get_store_metrics(self, store_id: str, db: Session) -> dict[str, float | int]:
        """Return visit and conversion metrics for a store."""

        counts_statement = select(
            func.count(distinct(VisitorSession.visitor_id)),
            func.count().filter(VisitorSession.session_end.is_(None)),
            func.count().filter(VisitorSession.converted.is_(True)),
        ).where(VisitorSession.store_id == store_id)

        unique_visitors, active_visitors, converted_visitors = db.execute(counts_statement).one()

        duration_statement = select(
            VisitorSession.session_start,
            VisitorSession.session_end,
        ).where(
            VisitorSession.store_id == store_id,
            VisitorSession.session_end.is_not(None),
        )
        closed_sessions = db.execute(duration_statement).all()

        if closed_sessions:
            total_duration_seconds = 0.0
            for session_start, session_end in closed_sessions:
                start = session_start
                end = session_end
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)
                total_duration_seconds += (end - start).total_seconds()

            avg_session_duration_seconds = total_duration_seconds / len(closed_sessions)
        else:
            avg_session_duration_seconds = 0.0

        conversion_rate = (
            (converted_visitors / unique_visitors) * 100 if unique_visitors else 0.0
        )

        return {
            "unique_visitors": int(unique_visitors or 0),
            "active_visitors": int(active_visitors or 0),
            "converted_visitors": int(converted_visitors or 0),
            "conversion_rate": float(conversion_rate),
            "avg_session_duration_seconds": float(avg_session_duration_seconds),
        }