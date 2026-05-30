from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def create_db_engine(database_url: str) -> Engine:
    """Create the SQLAlchemy engine for the configured database URL."""

    engine_kwargs: dict[str, object] = {
        "echo": False,
        "pool_pre_ping": True,
    }
    if make_url(database_url).drivername.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    return create_engine(database_url, **engine_kwargs)


engine: Engine = create_db_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for FastAPI request dependencies."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()