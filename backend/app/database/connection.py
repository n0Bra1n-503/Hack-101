"""Database connection and engine configuration for SkyGuard AI."""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from backend.app.core.config import settings

logger = logging.getLogger("skyguard.database")

# Configure database engine
connect_args = {}
engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    **engine_kwargs,
)

Base = declarative_base()


def init_db() -> None:
    """Create all registered database tables in the configured database."""
    # Import all models to ensure registration with Base.metadata
    import backend.app.models  # noqa: F401

    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
