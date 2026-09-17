"""Development-only token issuance for the REST control plane.

Enabled only when ``APP_ENV=development`` and explicitly opted in. Every hosted
environment (staging and production) must obtain access tokens from the
configured external OAuth identity provider; this endpoint is never available
there. Purpose: let the local demo UI and tests act as a chosen
Principal through the same signed-token path used everywhere else.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_rest_auth, rest_signing_secret
from app.config import settings
from app.db.models import Principal, PrincipalStatus, Tenant
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/me", dependencies=[Depends(require_rest_auth)])
def who_am_i(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return the authenticated principal + server-derived tenant context.

    In an enforced deployment an unauthenticated call returns 401. In the local
    development demo (auth not enforced) it returns an unauthenticated marker so
    the UI can offer the demo identity switcher without fabricating authority.
    """
    principal = getattr(request.state, "principal", None)
    if principal is None:
        return {"authenticated": False, "principal": None, "tenant_id": None, "tenant_name": None}
    tenant = db.get(Tenant, principal.tenant_id)
    return {
        "authenticated": True,
        "principal": {"id": str(principal.id), "name": principal.name, "external_id": principal.external_id, "type": principal.type.value if hasattr(principal.type, "value") else str(principal.type)},
        "tenant_id": str(principal.tenant_id),
        "tenant_name": tenant.name if tenant else None,
    }


class DevTokenRequest(BaseModel):
    principal_id: str | None = None
    external_id: str | None = None


class DevTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


@router.post("/dev-token", response_model=DevTokenResponse)
def issue_dev_token(payload: DevTokenRequest, db: Session = Depends(get_db)) -> DevTokenResponse:
    """Issue a short-lived development token for a Principal (development only)."""
    if settings.app_env != "development" or not settings.dev_token_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not available")
    secret = rest_signing_secret()
    if secret is None:  # pragma: no cover - unreachable outside production
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Signing key not configured")

    if payload.principal_id:
        principal = db.get(Principal, payload.principal_id)
    elif payload.external_id:
        principal = db.scalar(select(Principal).where(Principal.external_id == payload.external_id))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="principal_id or external_id required")
    if principal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Principal not found")
    if principal.status != PrincipalStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Principal is not active")

    now = datetime.now(timezone.utc)
    expires_in = 3600
    claims = {
        "sub": principal.external_id,
        "iss": settings.mcp_auth_issuer,
        "aud": settings.mcp_auth_audience,
        "scope": settings.mcp_auth_required_scope,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }
    token = jwt.encode(claims, secret, algorithm="HS256")
    return DevTokenResponse(access_token=token, expires_in=expires_in)
