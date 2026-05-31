from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.api.anomalies import router as anomalies_router
from app.api.events import router as events_router
from app.api.heatmap import router as heatmap_router
from app.api.funnel import router as funnel_router
from app.api.pipeline import router as pipeline_router
from app.api.stores import router as analytics_stores_router
from app.api.metrics import router as metrics_router
from app.api.transactions import router as transactions_router
from app.core.middleware import add_request_logging_middleware
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle events."""

    # Ensure schema exists for local and container runs before serving requests.
    Base.metadata.create_all(bind=engine)
    logger.info("Store Intelligence API is starting")
    yield
    logger.info("Store Intelligence API is shutting down")


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
add_request_logging_middleware(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(anomalies_router)
app.include_router(events_router)
app.include_router(heatmap_router)
app.include_router(funnel_router)
app.include_router(pipeline_router)
app.include_router(analytics_stores_router)
app.include_router(metrics_router)
app.include_router(transactions_router)


@app.get("/")
def root() -> dict[str, str]:
    """Return a simple readiness message for the API root."""

    return {"message": "Store Intelligence API Running"}


@app.get("/health")
def health() -> dict[str, str]:
    """Return the service health status."""

    return {"status": "healthy"}
