from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "agentos-api"}


def test_version_endpoint() -> None:
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert response.json()["name"] == "AgentOS API"
    assert response.json()["version"] == "0.1.0"


def test_readiness_endpoint_reports_database_readiness(monkeypatch) -> None:
    import app.main as main

    ready_engine = create_engine("sqlite://")
    monkeypatch.setattr(main, "engine", ready_engine)
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "service": "agentos-api"}


def test_readiness_endpoint_fails_closed_without_database(monkeypatch) -> None:
    import app.main as main

    monkeypatch.setattr(main, "engine", None)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database is not configured"
