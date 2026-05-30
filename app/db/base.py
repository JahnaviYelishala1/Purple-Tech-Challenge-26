"""Database metadata import hook for ORM model registration.

Importing this module ensures SQLAlchemy sees all model definitions before
metadata is used by migrations or table creation.
"""

from app.models.base import Base
from app.models.event import Event  # noqa: F401
from app.models.session import VisitorSession  # noqa: F401
from app.models.store import Store  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401

__all__ = ["Base", "Event", "VisitorSession", "Store", "Transaction"]