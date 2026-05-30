from pydantic import BaseModel, Field


class ZoneHeatmapMetric(BaseModel):
    """Aggregated heatmap metrics for a single store zone."""

    zone_id: str = Field(description="Zone identifier.")
    visit_count: int = Field(description="Count of ZONE_ENTER events for the zone.")
    avg_dwell_seconds: float = Field(description="Average dwell time in seconds for the zone.")
    normalized_score: float = Field(description="Zone score normalized against the busiest zone.")


class StoreHeatmapResponse(BaseModel):
    """Response payload for store heatmap analytics."""

    zones: list[ZoneHeatmapMetric] = Field(description="Zone-level heatmap metrics.")
    data_confidence: str = Field(description="Data confidence level for the heatmap.")