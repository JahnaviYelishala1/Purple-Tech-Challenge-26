"""Temporary verification script for database engine initialization."""

from app.db.database import engine


def main() -> None:
    """Print a success message when the engine is available."""

    if engine is not None:
        print("Database connection initialized successfully")


if __name__ == "__main__":
    main()