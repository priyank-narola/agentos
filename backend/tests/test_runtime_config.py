"""Production runtime configuration gates.

These tests exercise Settings directly so production guardrails are verified
without mutating the process-wide environment used by other API tests.
"""

import pytest

from app.config import RuntimeConfigurationError, Settings, validate_runtime_configuration


def production_settings(**overrides) -> Settings:
    values = {
        "app_env": "production",
        "database_url": "postgresql+psycopg://user:pass@db.example.test:5432/action_control",
        "frontend_origin": "https://app.example.test",
        "mcp_auth_issuer": "https://identity.example.test",
        "mcp_auth_audience": "https://api.example.test",
        "mcp_auth_jwks_url": "https://identity.example.test/.well-known/jwks.json",
        "webhook_secret": "production-webhook-secret",
        "dev_token_enabled": False,
        "rate_limit_max": 600,
        "rate_limit_window_seconds": 60,
        "log_level": "INFO",
        "log_format": "json",
    }
    values.update(overrides)
    return Settings(**values)


def staging_settings(**overrides) -> Settings:
    values = {
        "app_env": "staging",
        "database_url": "postgresql+psycopg://user:pass@db.example.test:5432/action_control",
        "frontend_origin": "https://staging.example.test",
        "mcp_auth_issuer": "https://identity.example.test",
        "mcp_auth_audience": "https://api.staging.example.test",
        "mcp_auth_jwks_url": "https://identity.example.test/.well-known/jwks.json",
        "webhook_secret": "staging-webhook-secret",
        "dev_token_enabled": False,
        "rate_limit_max": 600,
        "rate_limit_window_seconds": 60,
        "log_level": "INFO",
        "log_format": "json",
    }
    values.update(overrides)
    return Settings(**values)


def test_production_configuration_accepts_explicit_safe_settings() -> None:
    validate_runtime_configuration(production_settings())


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"database_url": "sqlite:///unsafe.db"}, "DATABASE_URL"),
        ({"frontend_origin": "http://app.example.test"}, "FRONTEND_ORIGIN"),
        ({"mcp_auth_jwks_url": "", "mcp_auth_public_key": "", "mcp_auth_secret_key": ""}, "MCP_AUTH_SECRET_KEY"),
        ({"dev_token_enabled": True}, "DEV_TOKEN_ENABLED"),
        ({"webhook_secret": "sandbox-webhook-secret-change-me"}, "WEBHOOK_SECRET"),
        ({"rate_limit_max": 0}, "RATE_LIMIT_MAX"),
        ({"database_pool_size": 0}, "database pool"),
        ({"database_max_overflow": -1}, "database pool"),
        ({"database_pool_recycle_seconds": 0}, "database pool"),
    ],
)
def test_production_configuration_rejects_unsafe_values(overrides, message) -> None:
    with pytest.raises(RuntimeConfigurationError, match=message):
        validate_runtime_configuration(production_settings(**overrides))


def test_non_production_configuration_keeps_local_development_available() -> None:
    validate_runtime_configuration(Settings(app_env="development", database_url=""))


def test_staging_configuration_accepts_explicit_safe_hosted_settings() -> None:
    validate_runtime_configuration(staging_settings())


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"database_url": "sqlite:///unsafe.db"}, "DATABASE_URL"),
        ({"frontend_origin": "http://staging.example.test"}, "FRONTEND_ORIGIN"),
        ({"mcp_auth_jwks_url": "", "mcp_auth_public_key": "", "mcp_auth_secret_key": ""}, "MCP_AUTH_SECRET_KEY"),
        ({"webhook_secret": "sandbox-webhook-secret-change-me"}, "WEBHOOK_SECRET"),
        ({"log_format": "plain"}, "LOG_FORMAT"),
    ],
)
def test_staging_configuration_rejects_unsafe_hosted_values(overrides, message) -> None:
    with pytest.raises(RuntimeConfigurationError, match=message):
        validate_runtime_configuration(staging_settings(**overrides))


def test_staging_configuration_rejects_development_token_issuance() -> None:
    with pytest.raises(RuntimeConfigurationError, match="DEV_TOKEN_ENABLED"):
        validate_runtime_configuration(Settings(app_env="staging", dev_token_enabled=True))


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"log_format": "plain"}, "LOG_FORMAT"),
        ({"log_level": "VERBOSE"}, "LOG_LEVEL"),
    ],
)
def test_production_configuration_rejects_unsafe_logging(overrides, message) -> None:
    with pytest.raises(RuntimeConfigurationError, match=message):
        validate_runtime_configuration(production_settings(**overrides))
