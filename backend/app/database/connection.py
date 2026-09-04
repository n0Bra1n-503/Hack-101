"""Database connection and engine configuration for SkyGuard AI."""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from backend.app.core.config import settings

logger = logging.getLogger("skyguard.database")

# Configure database engine
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

Base = declarative_base()


def init_db() -> None:
    """Create all registered database tables in the configured database."""
    # Import all models to ensure registration with Base.metadata
    import backend.app.models.reading  # noqa: F401

    logger.info(f"Initializing database schema at {settings.DATABASE_URL}...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
