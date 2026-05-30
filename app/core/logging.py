"""Centralized structured logging utilities."""

from __future__ import annotations

import logging
from logging import Logger

from pythonjsonlogger.jsonlogger import JsonFormatter


_LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
_RENAME_FIELDS = {
    "asctime": "timestamp",
    "levelname": "level",
    "message": "message",
}


def _build_handler() -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(_LOG_FORMAT, rename_fields=_RENAME_FIELDS))
    return handler


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger for JSON output."""

    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    if not root_logger.handlers:
        root_logger.addHandler(_build_handler())
        return

    for handler in root_logger.handlers:
        handler.setFormatter(JsonFormatter(_LOG_FORMAT, rename_fields=_RENAME_FIELDS))


def get_logger(name: str) -> Logger:
    """Return a configured logger instance without duplicate handlers."""

    logger = logging.getLogger(name)
    logger.setLevel(logging.getLogger().level or logging.INFO)
    logger.propagate = True
    return logger