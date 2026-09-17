"""Tests for the secret-free launch readiness summary."""

from app.api import launch_readiness as readiness_api
from app.config import Settings


def _statuses(summary: dict) -> dict[str, str]:
    return {item["id"]: item["status"] for item in summary["checks"]}


def test_launch_readiness_marks_local_sandbox_as_not_launchable(monkeypatch) -> None:
    monkeypatch.setattr(
        readiness_api,
        "settings",
        Settings(app_env="development", database_url="sqlite:///local.db"),
    )

    summary = readiness_api.launch_readiness()

    assert summary["launch_ready"] is False
    assert summary["blockers"] == 3
    assert summary["pending"] == 4
    assert _statuses(summary) == {
        "environment": "BLOCKED",
        "database": "BLOCKED",
        "identity": "BLOCKED",
        "zendesk": "PENDING",
        "stripe": "PENDING",
        "pilot": "PENDING",
        "data_controls": "PENDING",
    }


def test_launch_readiness_requires_all_operational_controls(monkeypatch) -> None:
    monkeypatch.setattr(
        readiness_api,
        "settings",
        Settings(
            app_env="production",
            database_url="postgresql+psycopg://user:pass@db.example.test:5432/action_control",
            mcp_auth_jwks_url="https://identity.example.test/.well-known/jwks.json",
            zendesk_context_connector_enabled=True,
            zendesk_subdomain="support-example",
            zendesk_oauth_access_token="test-zendesk-token",
            stripe_refund_connector_enabled=True,
            stripe_secret_key="sk_test_example",
        ),
    )

    summary = readiness_api.launch_readiness()

    assert summary["launch_ready"] is False
    assert summary["blockers"] == 0
    assert summary["pending"] == 2
    assert _statuses(summary)["zendesk"] == "READY"
    assert _statuses(summary)["stripe"] == "READY"


def test_launch_readiness_does_not_treat_enabled_connectors_as_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        readiness_api,
        "settings",
        Settings(
            app_env="staging",
            database_url="postgresql+psycopg://user:pass@db.example.test:5432/action_control",
            zendesk_context_connector_enabled=True,
            stripe_refund_connector_enabled=True,
            stripe_api_base="http://insecure.example.test",
        ),
    )

    summary = readiness_api.launch_readiness()

    assert _statuses(summary)["zendesk"] == "BLOCKED"
    assert _statuses(summary)["stripe"] == "BLOCKED"
