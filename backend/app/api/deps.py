"""REST control-plane authentication dependencies (W1/W3).

Uses the same OAuth2.1 Bearer token architecture as the MCP path (TokenValidator)
and resolves the authenticated Principal from the verified ``sub`` claim. No second
identity system is introduced.

Enforcement model:
- Attach ``require_rest_auth`` to every secured control-plane router.
- Authentication is enforced whenever ``is_rest_auth_required()`` is true:
  any non-development deployment (APP_ENV != development) or REST_AUTH_REQUIRED.
- In development the demo/UI can run unauthenticated by explicit operator choice;
  this posture is never available in production-like environments.
- Tenant identity is always derived from the authenticated Principal when
  authentication is active; client X-Tenant-ID / ?tenant_id are never authority.
"""

from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import AuthError, TokenValidator
from app.config import settings
from app.db.models import Principal, PrincipalStatus
from app.db.session import get_db

REST_DEV_SECRET = "agentos-local-dev-secret"


def is_rest_auth_required() -> bool:
    """True when REST bearer authentication must be enforced."""
    env_flag = _env_flag("REST_AUTH_REQUIRED")
    if env_flag is not None:
        return env_flag
    return settings.app_env != "development"


def _env_flag(name: str) -> bool | None:
    import os
    raw = os.getenv(name, "")
    if raw.lower() in {"1", "true", "yes"}:
        return True
    if raw.lower() in {"0", "false", "no"}:
        return False
    return None


def rest_signing_secret() -> str | None:
    """HMAC secret for REST/MCP token verification, or None (fail closed)."""
    if settings.mcp_auth_secret_key:
        return settings.mcp_auth_secret_key
    if settings.app_env != "production":
        return REST_DEV_SECRET
    return None


def _resolve_principal(sub: str, db: Session) -> Principal | None:
    principal = db.scalar(select(Principal).where(Principal.external_id == sub))
    if principal is not None:
        return principal
    try:
        return db.scalar(select(Principal).where(Principal.id == UUID(sub)))
    except ValueError:
        return None


def _authenticate(authorization: str | None, db: Session) -> Principal:
    secret = rest_signing_secret()
    if secret is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is not configured on this deployment",
        )
    if not authorization or not authorization.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": 'Bearer realm="AgentOS"'},
            detail="Missing Authorization header",
        )
    validator = TokenValidator(secret_key=secret)
    try:
        claims = validator.validate_token(authorization.strip())
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc

    principal = _resolve_principal(claims.sub, db)
    if principal is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authenticated principal not found")
    if principal.status != PrincipalStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Principal is not active")
    return principal


def require_rest_auth(request: Request, db: Session = Depends(get_db)) -> None:
    """Router-level dependency enforcing REST authentication when required."""
    if not is_rest_auth_required():
        return
    principal = _authenticate(request.headers.get("authorization"), db)
    request.state.principal = principal
    request.state.tenant_id = principal.tenant_id


def get_current_principal(request: Request) -> Principal:
    """Return the authenticated Principal (requires enforced auth)."""
    principal = getattr(request.state, "principal", None)
    if principal is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return principal


def get_current_tenant(request: Request) -> UUID:
    """Server-derived tenant scope for the authenticated Principal."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return tenant_id
