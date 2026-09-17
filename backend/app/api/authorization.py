"""Reusable FastAPI role gates for sensitive control-plane operations."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import TenantRole
from app.db.session import get_db
from app.services.authorization import RoleAuthorizationError, require_any_role


def require_tenant_roles(roles: set[TenantRole]) -> Callable:
    """Build a dependency that enforces roles outside local development.

    Development intentionally remains usable for synthetic demo data. Staging
    and production require both verified authentication (provided by the
    router-level REST gate) and an explicit database-backed tenant role.
    """

    def dependency(request: Request, db: Session = Depends(get_db)) -> None:
        if settings.app_env == "development":
            return
        principal = getattr(request.state, "principal", None)
        tenant_id = getattr(request.state, "tenant_id", None)
        if principal is None or tenant_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated tenant context is required")
        try:
            require_any_role(db, tenant_id=tenant_id, principal_id=principal.id, roles=roles)
        except RoleAuthorizationError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return dependency
