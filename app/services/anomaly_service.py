from datetime import timedelta, timezone

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.event import Event as EventModel
from app.models.session import VisitorSession
from app.schemas.anomaly import Anomaly, StoreAnomaliesResponse


class AnomalyService:
    """Service for detecting store-level operational anomalies."""

    def get_store_anomalies(self, store_id: str, db: Session) -> StoreAnomaliesResponse:
        """Return detected anomalies for a store."""

        anomalies: list[Anomaly] = []

        latest_event_statement = select(func.max(EventModel.timestamp)).where(EventModel.store_id == store_id)
        latest_event_timestamp = db.execute(latest_event_statement).scalar_one()
        if latest_event_timestamp is None:
            return StoreAnomaliesResponse(anomalies=[])

        if latest_event_timestamp.tzinfo is None:
            latest_event_timestamp = latest_event_timestamp.replace(tzinfo=timezone.utc)

        recent_window_start = latest_event_timestamp - timedelta(minutes=30)
        queue_window_start = latest_event_timestamp - timedelta(minutes=15)

        historical_zones_statement = select(func.count()).where(
            EventModel.store_id == store_id,
            EventModel.zone_id.is_not(None),
            EventModel.is_staff.is_(False),
        )
        historical_zone_count = int(db.execute(historical_zones_statement).scalar_one() or 0)

        recent_zone_enter_statement = select(func.count()).where(
            EventModel.store_id == store_id,
            EventModel.event_type == "ZONE_ENTER",
            EventModel.timestamp >= recent_window_start,
            EventModel.is_staff.is_(False),
        )
        recent_zone_enter_count = int(db.execute(recent_zone_enter_statement).scalar_one() or 0)

        if historical_zone_count > 0 and recent_zone_enter_count == 0:
            anomalies.append(
                Anomaly(
                    anomaly_type="DEAD_ZONE",
                    severity="WARN",
                    description="A historically active zone has received no recent zone entry activity.",
                    suggested_action="Investigate merchandising and customer flow.",
                )
            )

        queue_spike_statement = select(func.count()).where(
            EventModel.store_id == store_id,
            EventModel.event_type == "BILLING_QUEUE_JOIN",
            EventModel.timestamp >= queue_window_start,
            EventModel.is_staff.is_(False),
        )
        queue_spike_count = int(db.execute(queue_spike_statement).scalar_one() or 0)

        if queue_spike_count > 5:
            anomalies.append(
                Anomaly(
                    anomaly_type="QUEUE_SPIKE",
                    severity="CRITICAL",
                    description="Billing queue join activity exceeded the threshold in the last 15 minutes.",
                    suggested_action="Open additional billing counters.",
                )
            )

        metrics_statement = select(
            func.count(distinct(VisitorSession.visitor_id)).label("unique_visitors"),
            func.count().filter(VisitorSession.converted.is_(True)).label("converted_visitors"),
        ).where(
            VisitorSession.store_id == store_id,
            VisitorSession.is_staff.is_(False),
        )
        unique_visitors, converted_visitors = db.execute(metrics_statement).one()
        unique_visitors = int(unique_visitors or 0)
        converted_visitors = int(converted_visitors or 0)
        conversion_rate = (converted_visitors / unique_visitors * 100) if unique_visitors else 0.0

        if unique_visitors > 0 and conversion_rate < 20:
            anomalies.append(
                Anomaly(
                    anomaly_type="CONVERSION_DROP",
                    severity="WARN",
                    description="Store conversion rate is below the target threshold.",
                    suggested_action="Review customer journey and checkout process.",
                )
            )

        return StoreAnomaliesResponse(anomalies=anomalies)