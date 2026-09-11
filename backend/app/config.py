import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

_is_production = os.getenv("APP_ENV", "development") == "production"


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

    # MCP Auth settings
    mcp_auth_enabled: bool = os.getenv("MCP_AUTH_ENABLED", "false").lower() in ("true", "1", "yes")
    mcp_auth_issuer: str = os.getenv("MCP_AUTH_ISSUER", "https://auth.agentos.com")
    mcp_auth_audience: str = os.getenv("MCP_AUTH_AUDIENCE", "https://agentos-api-qm2r.onrender.com")
    mcp_auth_jwks_url: str = os.getenv("MCP_AUTH_JWKS_URL", "https://auth.agentos.com/.well-known/jwks.json")
    mcp_auth_required_scope: str = os.getenv("MCP_AUTH_REQUIRED_SCOPE", "agentos:execute")
    mcp_auth_public_key: str = os.getenv("MCP_AUTH_PUBLIC_KEY", "")
    mcp_auth_secret_key: str = os.getenv("MCP_AUTH_SECRET_KEY", "")

    # Abuse protection (bounded, single-instance)
    rate_limit_max: int = int(os.getenv("RATE_LIMIT_MAX", "600"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    # Webhook verification (sandbox provider source). Replace in any real deployment.
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "" if _is_production else "sandbox-webhook-secret-change-me")
    webhook_max_skew_seconds: int = int(os.getenv("WEBHOOK_MAX_SKEW_SECONDS", "300"))

    # Dev token endpoint: disabled by default; set DEV_TOKEN_ENABLED=true to opt in.
    dev_token_enabled: bool = os.getenv("DEV_TOKEN_ENABLED", "false").lower() in ("true", "1", "yes")


settings = Settings()
