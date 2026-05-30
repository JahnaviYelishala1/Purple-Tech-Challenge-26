from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event as EventModel
from app.schemas.event import EventType
from app.schemas.event import Event as EventSchema
from app.services.session_service import SessionService


class EventIngestionService:
    """Service for ingesting validated retail analytics events."""

    def ingest_events(self, events: Sequence[EventSchema], db: Session) -> dict[str, int]:
        """Insert non-duplicate events and return ingestion statistics."""

        total_received = len(events)
        if total_received == 0:
            return {"total_received": 0, "inserted": 0, "duplicates": 0}

        incoming_ids = [str(event.event_id) for event in events]
        existing_ids = set(
            db.scalars(
                select(EventModel.event_id).where(EventModel.event_id.in_(incoming_ids))
            ).all()
        )

        seen_ids = set(existing_ids)
        rows_to_insert: list[EventModel] = []
        duplicates = 0
        session_service = SessionService()

        for event in events:
            event_id = str(event.event_id)
            if event_id in seen_ids:
                duplicates += 1
                continue

            seen_ids.add(event_id)
            rows_to_insert.append(
                EventModel(
                    event_id=event_id,
                    store_id=event.store_id,
                    camera_id=event.camera_id,
                    visitor_id=event.visitor_id,
                    event_type=event.event_type.value,
                    timestamp=event.timestamp,
                    zone_id=event.zone_id,
                    dwell_ms=event.dwell_ms,
                    is_staff=event.is_staff,
                    confidence=event.confidence,
                    queue_depth=event.metadata.queue_depth if event.metadata else None,
                    sku_zone=event.metadata.sku_zone if event.metadata else None,
                    session_seq=event.metadata.session_seq if event.metadata else None,
                )
            )

            if event.event_type is EventType.ENTRY:
                session_service.handle_entry_event(event, db)
            elif event.event_type is EventType.EXIT:
                session_service.handle_exit_event(event, db)

        if rows_to_insert:
            db.add_all(rows_to_insert)

        db.commit()

        inserted = len(rows_to_insert)
        return {
            "total_received": total_received,
            "inserted": inserted,
            "duplicates": duplicates,
        }
