from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


def _database_url() -> str:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be configured before creating a database engine")
    return settings.database_url


def _engine_options() -> dict[str, int | bool]:
    """Return database-safe pooling options for the configured PostgreSQL runtime.

    SQLite unit tests create their own engine. Production startup already
    requires PostgreSQL, where bounded pool settings prevent each application
    process from opening an unbounded number of managed-database connections.
    """
    return {
        "pool_pre_ping": True,
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_recycle": settings.database_pool_recycle_seconds,
    }


engine = create_engine(_database_url(), **_engine_options()) if settings.database_url else None
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) if engine else None


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL must be configured before opening a database session")
    with SessionLocal() as session:
        yield session
