"""Compatibility module that exposes SQLAlchemy database primitives."""

from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase

from app.db.session import engine


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


__all__ = ["Base", "Engine", "engine"]