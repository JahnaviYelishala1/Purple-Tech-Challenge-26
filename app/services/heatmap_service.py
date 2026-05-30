from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.event import Event as EventModel
from app.models.session import VisitorSession
from app.schemas.heatmap import StoreHeatmapResponse, ZoneHeatmapMetric


class HeatmapService:
    """Service for computing zone-level store heatmap analytics."""

    def get_store_heatmap(self, store_id: str, db: Session) -> StoreHeatmapResponse:
        """Return heatmap metrics for a store."""

        zone_statement = select(
            func.upper(EventModel.zone_id).label("zone_id"),
            func.sum(
                case((EventModel.event_type == "ZONE_ENTER", 1), else_=0)
            ).label("visit_count"),
            func.avg(
                case((EventModel.event_type == "ZONE_DWELL", EventModel.dwell_ms), else_=None)
            ).label("avg_dwell_ms"),
        ).where(
            EventModel.store_id == store_id,
            EventModel.zone_id.is_not(None),
            EventModel.event_type.in_(["ZONE_ENTER", "ZONE_DWELL"]),
        ).group_by(func.upper(EventModel.zone_id))

        zone_rows = db.execute(zone_statement).all()

        zone_metrics: list[ZoneHeatmapMetric] = []
        max_visit_count = 0
        for zone_id, visit_count, avg_dwell_ms in zone_rows:
            visits = int(visit_count or 0)
            max_visit_count = max(max_visit_count, visits)
            zone_metrics.append(
                ZoneHeatmapMetric(
                    zone_id=str(zone_id),
                    visit_count=visits,
                    avg_dwell_seconds=float(avg_dwell_ms or 0.0) / 1000.0,
                    normalized_score=0.0,
                )
            )

        if max_visit_count > 0:
            for metric in zone_metrics:
                metric.normalized_score = (metric.visit_count / max_visit_count) * 100

        session_count_statement = select(func.count()).where(VisitorSession.store_id == store_id)
        total_sessions = int(db.execute(session_count_statement).scalar_one() or 0)
        data_confidence = "LOW" if total_sessions < 20 else "HIGH"

        return StoreHeatmapResponse(zones=zone_metrics, data_confidence=data_confidence)