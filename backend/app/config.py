import os
from dataclasses import dataclass


def normalize_database_url(url: str) -> str:
    """Select the installed Psycopg 3 SQLAlchemy dialect for PostgreSQL URLs."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "AgentOS API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    app_env: str = os.getenv("APP_ENV", "development")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    database_url: str = normalize_database_url(os.getenv("DATABASE_URL", ""))


settings = Settings()
