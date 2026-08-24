from app.config import normalize_database_url


def test_postgres_urls_use_psycopg3_dialect() -> None:
    assert normalize_database_url("postgres://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"
    assert normalize_database_url("postgresql://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"
    assert normalize_database_url("postgresql+psycopg://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"
