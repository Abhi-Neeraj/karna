"""SQLAlchemy database infrastructure for the KARNA backend."""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeMeta, Session, declarative_base, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

_connect_args: dict[str, bool] = {}
if settings.database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine: Engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    echo=settings.debug,
)
"""Configured SQLAlchemy engine for application persistence."""

SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)
"""Factory for database sessions scoped to individual requests or operations."""

Base: DeclarativeMeta = declarative_base()
"""Declarative base class inherited by all KARNA SQLAlchemy models."""


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and close it after the requesting operation ends.

    FastAPI route dependencies use this generator to receive an isolated
    SQLAlchemy session for each request.

    Yields:
        An active SQLAlchemy database session.
    """
    database_session = SessionLocal()
    try:
        yield database_session
    finally:
        database_session.close()


def init_db() -> None:
    """Create all tables registered on the KARNA declarative metadata.

    Model modules must be imported before this function is called so their
    mapped tables are registered on ``Base.metadata``.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If table initialization fails.
    """
    logger.info("Initializing KARNA database at %s", settings.database_url)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        logger.exception("Failed to initialize the KARNA database")
        raise
    logger.info("KARNA database initialization completed")
