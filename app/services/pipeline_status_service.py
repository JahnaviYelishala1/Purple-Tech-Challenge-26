from __future__ import annotations

import json
from pathlib import Path

from datetime import datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.event import Event as EventModel
from app.models.session import VisitorSession

from pipeline.camera_roles import camera_ids_for_role, load_camera_roles, role_label


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CAMERA_MAPPING_PATH = PROJECT_ROOT / "camera_mapping.json"
TARGET_ROLES = ("ENTRANCE", "BILLING", "ZONE", "EXIT")


class PipelineStatusService:
    """Build a small CCTV pipeline status view for the dashboard."""

    def _load_camera_labels(self) -> dict[str, str]:
        labels: dict[str, str] = {}
        load_camera_roles()
        for role in TARGET_ROLES:
            for camera_id in camera_ids_for_role(role):
                labels[camera_id] = f"{camera_id} ({role_label(role)})"

        if labels:
            return labels

        if not CAMERA_MAPPING_PATH.exists():
            return {}

        try:
            raw_mapping = json.loads(CAMERA_MAPPING_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

        for camera_id, raw_label in raw_mapping.items():
            labels[str(camera_id)] = str(raw_label).replace("_", " ").title()
        return labels

    def _load_latest_event(self, db: Session, store_id: str, *, event_type: str | None = None, camera_id: str | None = None) -> EventModel | None:
        statement = select(EventModel).where(EventModel.store_id == store_id)
        if event_type is not None:
            statement = statement.where(EventModel.event_type == event_type)
        if camera_id is not None:
            statement = statement.where(EventModel.camera_id == camera_id)
        statement = statement.order_by(EventModel.timestamp.desc(), EventModel.id.desc())
        return db.scalars(statement).first()

    def _camera_status(self, db: Session, store_id: str, camera_id: str, label: str) -> dict[str, object]:
        latest_event = self._load_latest_event(db, store_id, camera_id=camera_id)
        active = latest_event is not None
        return {
            "camera_id": camera_id,
            "label": label,
            "active": active,
            "status": "Active" if active else "Idle",
            "last_event_id": latest_event.event_id if latest_event is not None else None,
            "last_track_id": latest_event.visitor_id if latest_event is not None else None,
            "last_event_type": latest_event.event_type if latest_event is not None else None,
            "last_seen": latest_event.timestamp if latest_event is not None else None,
        }

    def get_store_pipeline_status(self, store_id: str, db: Session) -> dict[str, object]:
        labels = self._load_camera_labels()
        latest_event = self._load_latest_event(db, store_id)
        if latest_event is not None:
            latest_timestamp = latest_event.timestamp
            if latest_timestamp.tzinfo is None:
                latest_timestamp = latest_timestamp.replace(tzinfo=timezone.utc)
            else:
                latest_timestamp = latest_timestamp.astimezone(timezone.utc)
            day_start = datetime.combine(latest_timestamp.date(), time.min, tzinfo=timezone.utc)
        else:
            day_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        cameras = [
            self._camera_status(db, store_id, camera_id=camera_id, label=labels.get(camera_id, camera_id))
            for camera_id in labels.keys()
        ]

        latest_entry = self._load_latest_event(db, store_id, event_type="ENTRY")
        latest_billing = self._load_latest_event(db, store_id, event_type="BILLING_QUEUE_JOIN")

        activity_statement = select(
            func.count(),
            func.count().filter(EventModel.event_type == "ENTRY"),
            func.count().filter(EventModel.event_type == "BILLING_QUEUE_JOIN"),
        ).where(
            EventModel.store_id == store_id,
            EventModel.timestamp >= day_start,
            EventModel.is_staff.is_(False),
        )
        total_events_today, entries_today, billing_today = db.execute(activity_statement).one()

        converted_sessions_statement = select(func.count()).where(
            VisitorSession.store_id == store_id,
            VisitorSession.converted.is_(True),
            VisitorSession.session_start >= day_start,
            VisitorSession.is_staff.is_(False),
        )
        purchases_today = int(db.execute(converted_sessions_statement).scalar_one() or 0)

        return {
            "cameras": cameras,
            "last_entry_event": (
                {
                    "event_id": latest_entry.event_id,
                    "track_id": latest_entry.visitor_id,
                    "camera_id": latest_entry.camera_id,
                    "event_type": latest_entry.event_type,
                    "last_seen": latest_entry.timestamp,
                }
                if latest_entry is not None
                else None
            ),
            "last_billing_event": (
                {
                    "event_id": latest_billing.event_id,
                    "track_id": latest_billing.visitor_id,
                    "camera_id": latest_billing.camera_id,
                    "event_type": latest_billing.event_type,
                    "last_seen": latest_billing.timestamp,
                }
                if latest_billing is not None
                else None
            ),
            "activity_summary": {
                "entries_today": int(entries_today or 0),
                "billing_interactions_today": int(billing_today or 0),
                "purchases_today": purchases_today,
                "total_events_today": int(total_events_today or 0),
            },
        }