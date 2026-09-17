import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

_is_hosted = os.getenv("APP_ENV", "development") in {"staging", "production"}
_DEFAULT_AUTH_ISSUER = "https://auth.agentos.com"
_DEFAULT_AUTH_AUDIENCE = "https://agentos-api-qm2r.onrender.com"
_SANDBOX_WEBHOOK_SECRET = "sandbox-webhook-secret-change-me"


class RuntimeConfigurationError(RuntimeError):
    """Raised when a production process would start in an unsafe configuration."""


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
    database_pool_size: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    database_max_overflow: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    database_pool_recycle_seconds: int = int(os.getenv("DATABASE_POOL_RECYCLE_SECONDS", "1800"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format: str = os.getenv("LOG_FORMAT", "json" if _is_hosted else "plain").lower()

    # MCP Auth settings
    mcp_auth_enabled: bool = os.getenv("MCP_AUTH_ENABLED", "false").lower() in ("true", "1", "yes")
    mcp_auth_issuer: str = os.getenv("MCP_AUTH_ISSUER", _DEFAULT_AUTH_ISSUER)
    mcp_auth_audience: str = os.getenv("MCP_AUTH_AUDIENCE", _DEFAULT_AUTH_AUDIENCE)
    mcp_auth_jwks_url: str = os.getenv("MCP_AUTH_JWKS_URL", "")
    mcp_auth_required_scope: str = os.getenv("MCP_AUTH_REQUIRED_SCOPE", "agentos:execute")
    mcp_auth_public_key: str = os.getenv("MCP_AUTH_PUBLIC_KEY", "")
    mcp_auth_secret_key: str = os.getenv("MCP_AUTH_SECRET_KEY", "")

    # Abuse protection (bounded, single-instance)
    rate_limit_max: int = int(os.getenv("RATE_LIMIT_MAX", "600"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    # Webhook verification (sandbox provider source). Replace in any real deployment.
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "" if _is_hosted else _SANDBOX_WEBHOOK_SECRET)
    webhook_max_skew_seconds: int = int(os.getenv("WEBHOOK_MAX_SKEW_SECONDS", "300"))

    # Dev token endpoint: disabled by default; set DEV_TOKEN_ENABLED=true to opt in.
    dev_token_enabled: bool = os.getenv("DEV_TOKEN_ENABLED", "false").lower() in ("true", "1", "yes")

    # Selected-pilot connector. It remains disabled by default, including in
    # production, until a design partner approves a test-mode integration.
    stripe_refund_connector_enabled: bool = os.getenv("STRIPE_REFUND_CONNECTOR_ENABLED", "false").lower() in ("true", "1", "yes")
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_api_base: str = os.getenv("STRIPE_API_BASE", "https://api.stripe.com")

    zendesk_context_connector_enabled: bool = os.getenv("ZENDESK_CONTEXT_CONNECTOR_ENABLED", "false").lower() in ("true", "1", "yes")
    zendesk_subdomain: str = os.getenv("ZENDESK_SUBDOMAIN", "")
    zendesk_oauth_access_token: str = os.getenv("ZENDESK_OAUTH_ACCESS_TOKEN", "")


settings = Settings()


def validate_runtime_configuration(current: Settings = settings) -> None:
    """Fail closed for unsafe hosted configuration.

    Local development intentionally remains easy to run. A process marked as
    staging and production, however, must not silently use placeholder identity
    settings, an in-memory database, an HTTP browser origin, a development
    token issuer, or a known sandbox webhook secret. Staging is an externally
    reachable environment too; delaying these checks until production creates
    an avoidable insecure deployment path.
    """
    allowed_environments = {"development", "test", "staging", "production"}
    if current.app_env not in allowed_environments:
        raise RuntimeConfigurationError(
            f"APP_ENV must be one of {sorted(allowed_environments)}, got {current.app_env!r}"
        )
    if current.app_env != "development" and current.dev_token_enabled:
        raise RuntimeConfigurationError("DEV_TOKEN_ENABLED must be false outside development")
    if current.app_env not in {"staging", "production"}:
        return

    errors: list[str] = []
    if not current.database_url.startswith("postgresql+"):
        errors.append("DATABASE_URL must use a PostgreSQL SQLAlchemy URL in hosted environments")
    if current.database_pool_size <= 0 or current.database_max_overflow < 0 or current.database_pool_recycle_seconds <= 0:
        errors.append("database pool size/recycle settings must be positive (max overflow may be zero)")

    origins = [origin.strip() for origin in current.frontend_origin.split(",") if origin.strip()]
    if not origins or any(not origin.startswith("https://") or origin == "*" for origin in origins):
        errors.append("FRONTEND_ORIGIN must contain one or more explicit HTTPS origins in hosted environments")

    if not current.mcp_auth_issuer or current.mcp_auth_issuer == _DEFAULT_AUTH_ISSUER:
        errors.append("MCP_AUTH_ISSUER must be explicitly configured in hosted environments")
    if not current.mcp_auth_audience or current.mcp_auth_audience == _DEFAULT_AUTH_AUDIENCE:
        errors.append("MCP_AUTH_AUDIENCE must be explicitly configured in hosted environments")
    if not any((current.mcp_auth_secret_key, current.mcp_auth_public_key, current.mcp_auth_jwks_url)):
        errors.append("configure MCP_AUTH_SECRET_KEY, MCP_AUTH_PUBLIC_KEY, or MCP_AUTH_JWKS_URL in hosted environments")
    if current.dev_token_enabled:
        errors.append("DEV_TOKEN_ENABLED must be false in hosted environments")
    if current.stripe_refund_connector_enabled:
        if not current.stripe_secret_key:
            errors.append("STRIPE_SECRET_KEY is required when the Stripe refund connector is enabled")
        if not current.stripe_api_base.startswith("https://"):
            errors.append("STRIPE_API_BASE must use HTTPS when the Stripe refund connector is enabled")
    if current.zendesk_context_connector_enabled:
        if not current.zendesk_subdomain:
            errors.append("ZENDESK_SUBDOMAIN is required when the Zendesk context connector is enabled")
        if not current.zendesk_oauth_access_token:
            errors.append("ZENDESK_OAUTH_ACCESS_TOKEN is required when the Zendesk context connector is enabled")
    if not current.webhook_secret or current.webhook_secret == _SANDBOX_WEBHOOK_SECRET:
        errors.append("WEBHOOK_SECRET must be a non-sandbox secret in hosted environments")
    if current.rate_limit_max <= 0 or current.rate_limit_window_seconds <= 0:
        errors.append("RATE_LIMIT_MAX and RATE_LIMIT_WINDOW_SECONDS must be positive")
    if current.log_level not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
        errors.append("LOG_LEVEL must be a standard Python logging level")
    if current.log_format != "json":
        errors.append("LOG_FORMAT must be json in hosted environments")

    if errors:
        raise RuntimeConfigurationError("Unsafe production configuration: " + "; ".join(errors))
