from pydantic import BaseModel, Field


class StoreMetricsResponse(BaseModel):
    """Response payload for store-level visitor session metrics."""

    unique_visitors: int = Field(description="Distinct visitors with sessions for the store.")
    active_visitors: int = Field(description="Sessions that are still active.")
    converted_visitors: int = Field(description="Sessions marked as converted.")
    conversion_rate: float = Field(description="Conversion percentage for the store.")
    avg_session_duration_seconds: float = Field(
        description="Average duration in seconds across closed sessions."
    )