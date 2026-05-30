from datetime import datetime

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    """Request payload for a single retail transaction."""

    transaction_id: str = Field(description="Unique transaction identifier.")
    store_id: str = Field(description="Store identifier associated with the transaction.")
    timestamp: datetime = Field(description="Transaction timestamp.")
    basket_value: float = Field(gt=0, description="Total basket value for the transaction.")


class TransactionIngestRequest(BaseModel):
    """Request payload for bulk transaction ingestion."""

    transactions: list[TransactionCreate] = Field(
        min_length=1,
        max_length=500,
        description="Transactions to ingest, up to 500 per request.",
    )