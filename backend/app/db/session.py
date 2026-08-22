from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


def _database_url() -> str:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be configured before creating a database engine")
    return settings.database_url


engine = create_engine(_database_url(), pool_pre_ping=True) if settings.database_url else None
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) if engine else None


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL must be configured before opening a database session")
    with SessionLocal() as session:
        yield session
