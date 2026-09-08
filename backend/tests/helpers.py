"""Shared test helpers (W8).

Small, deterministic helpers shared across test modules. They are importable as
``from tests.helpers import ...`` from any module under backend/tests.
"""

import time
import uuid

import jwt

from app.api.deps import REST_DEV_SECRET
from app.config import settings


def mint_rest_token(external_id: str, secret: str = REST_DEV_SECRET) -> str:
    """Mint a short-lived HS256 token for a Principal (same scheme as dev tokens)."""
    now = int(time.time())
    claims = {
        "sub": external_id,
        "iss": settings.mcp_auth_issuer,
        "aud": settings.mcp_auth_audience,
        "scope": settings.mcp_auth_required_scope,
        "iat": now,
        "exp": now + 3600,
    }
    return jwt.encode(claims, secret, algorithm="HS256")


def bearer(external_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {mint_rest_token(external_id)}"}


def new_id() -> str:
    return str(uuid.uuid4())
