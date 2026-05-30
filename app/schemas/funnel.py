from pydantic import BaseModel, Field


class FunnelStage(BaseModel):
    """A single stage in the store funnel."""

    stage: str = Field(description="Funnel stage name.")
    count: int = Field(description="Number of visitors or sessions in the stage.")
    dropoff_percentage: float = Field(description="Percentage dropoff from the previous stage.")


class StoreFunnelResponse(BaseModel):
    """Response payload for store funnel analytics."""

    stages: list[FunnelStage] = Field(description="Ordered funnel stages for the store.")