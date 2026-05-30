"""Initialize the database schema from SQLAlchemy metadata."""

import app.models  # noqa: F401
from app.db.database import Base, engine


def main() -> None:
    """Create all tables and report success."""

    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


if __name__ == "__main__":
    main()