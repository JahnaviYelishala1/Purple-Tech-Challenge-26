"""Structured request logging middleware for FastAPI."""

from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each request as a structured JSON event."""

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = str(uuid4())
        request.state.trace_id = trace_id
        start_time = perf_counter()

        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            logger.exception(
                "request_failed",
                extra={
                    "trace_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "latency_ms": round((perf_counter() - start_time) * 1000, 2),
                },
            )
            raise
        finally:
            logger.info(
                "request_completed",
                extra={
                    "trace_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "latency_ms": round((perf_counter() - start_time) * 1000, 2),
                },
            )


def add_request_logging_middleware(app: FastAPI) -> None:
    """Register request logging middleware on the FastAPI app."""

    app.add_middleware(RequestLoggingMiddleware)