from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.event import Event as EventModel
from app.models.session import VisitorSession


class FunnelService:
    """Service for computing store funnel analytics."""

    def get_store_funnel(self, store_id: str, db: Session) -> dict[str, list[dict[str, float | int | str]]]:
        """Return ordered funnel stages and dropoff percentages for a store."""

        stage_queries = [
            (
                "ENTRY",
                select(func.count(distinct(EventModel.visitor_id))).where(
                    EventModel.store_id == store_id,
                    EventModel.event_type == "ENTRY",
                ),
            ),
            (
                "ZONE_VISIT",
                select(func.count(distinct(EventModel.visitor_id))).where(
                    EventModel.store_id == store_id,
                    EventModel.event_type.in_(["ZONE_ENTER", "ZONE_DWELL"]),
                ),
            ),
            (
                "BILLING_QUEUE",
                select(func.count(distinct(EventModel.visitor_id))).where(
                    EventModel.store_id == store_id,
                    EventModel.event_type == "BILLING_QUEUE_JOIN",
                ),
            ),
            (
                "PURCHASE",
                select(func.count()).where(
                    VisitorSession.store_id == store_id,
                    VisitorSession.converted.is_(True),
                ),
            ),
        ]

        stage_counts: list[tuple[str, int]] = []
        for stage_name, statement in stage_queries:
            count_value = db.execute(statement).scalar_one()
            stage_counts.append((stage_name, int(count_value or 0)))

        stages: list[dict[str, float | int | str]] = []
        previous_count: int | None = None
        for stage_name, count_value in stage_counts:
            if previous_count not in (None, 0):
                count_value = min(count_value, previous_count)

            if previous_count in (None, 0):
                dropoff_percentage = 0.0
            else:
                dropoff_percentage = ((previous_count - count_value) / previous_count) * 100

            stages.append(
                {
                    "stage": stage_name,
                    "count": count_value,
                    "dropoff_percentage": float(dropoff_percentage),
                }
            )
            previous_count = count_value

        return {"stages": stages}