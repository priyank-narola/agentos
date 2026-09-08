"""Rate limiting / MCP abuse-protection tests."""

import time

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.api.ratelimit import FixedWindowRateLimiter, check_rate_limit

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    with TestingSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_fixed_window_limiter_blocks_over_limit_and_resets():
    limiter = FixedWindowRateLimiter(max_requests=3, window_seconds=1)
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is False  # over limit
    # A different key is not affected.
    assert limiter.allow("client-b") is True
    # After the window elapses the original key is allowed again.
    time.sleep(1.05)
    assert limiter.allow("client-a") is True


def test_rate_limit_dependency_wiring_returns_429():
    """Proving 429 is returned when the limit dependency denies a request."""
    def deny():
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Try again shortly.")

    app.dependency_overrides[check_rate_limit] = deny
    try:
        response = client.post("/api/v1/action-requests", json={})
        assert response.status_code == 429
    finally:
        app.dependency_overrides.pop(check_rate_limit, None)


def test_mcp_endpoint_rejects_with_429_when_denied():
    def deny():
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Try again shortly.")

    # mcp_app is a separate FastAPI instance mounted under /mcp.
    from app.api.mcp import mcp_app, check_rate_limit as mcp_check_rate_limit
    mcp_app.dependency_overrides[mcp_check_rate_limit] = deny
    try:
        response = client.post("/mcp/", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
        assert response.status_code == 429
    finally:
        mcp_app.dependency_overrides.pop(mcp_check_rate_limit, None)


@pytest.fixture(autouse=True)
def reset_db():
    with TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
