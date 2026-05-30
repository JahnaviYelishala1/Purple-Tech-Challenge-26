from pydantic import BaseModel, Field


class Anomaly(BaseModel):
    """A detected anomaly in store behavior analytics."""

    anomaly_type: str = Field(description="Type of anomaly detected.")
    severity: str = Field(description="Severity level of the anomaly.")
    description: str = Field(description="Human-readable anomaly description.")
    suggested_action: str = Field(description="Recommended remediation action.")


class StoreAnomaliesResponse(BaseModel):
    """Response payload for store anomaly detection."""

    anomalies: list[Anomaly] = Field(description="Detected anomalies for the store.")