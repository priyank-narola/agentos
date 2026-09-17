"""Tenant role administration endpoints.

The initial production ADMIN role must be created by a controlled provisioning
process, never by a public self-service endpoint.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.ratelimit import check_rate_limit
from app.api.authorization import require_tenant_roles
from app.db.models import DEFAULT_TENANT_ID, TenantRole
from app.db.session import get_db
from app.schemas import PrincipalRoleGrant, PrincipalRoleRevoke, PrincipalRoleSchema
from app.services.authorization import RoleAuthorizationError, RoleManagementService


router = APIRouter(prefix="/api/v1/roles", tags=["tenant-role-administration"])
admin_required = require_tenant_roles({TenantRole.ADMIN})


def service(db: Session = Depends(get_db)) -> RoleManagementService:
    return RoleManagementService(db)


def trusted_tenant(request: Request) -> UUID:
    return getattr(request.state, "tenant_id", None) or DEFAULT_TENANT_ID


@router.get("", response_model=list[PrincipalRoleSchema], dependencies=[Depends(admin_required)])
def list_role_assignments(request: Request, roles: RoleManagementService = Depends(service)) -> list[PrincipalRoleSchema]:
    return roles.list(trusted_tenant(request))


@router.post("", response_model=PrincipalRoleSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_rate_limit), Depends(admin_required)])
def grant_role(
    payload: PrincipalRoleGrant,
    request: Request,
    roles: RoleManagementService = Depends(service),
) -> PrincipalRoleSchema:
    principal = getattr(request.state, "principal", None)
    if principal is not None and payload.actor_principal_id != principal.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authenticated principal cannot grant roles as another user")
    try:
        return roles.grant(
            tenant_id=trusted_tenant(request),
            actor_principal_id=payload.actor_principal_id,
            principal_id=payload.principal_id,
            role=payload.role,
        )
    except RoleAuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(check_rate_limit), Depends(admin_required)])
def revoke_role(
    assignment_id: UUID,
    payload: PrincipalRoleRevoke,
    request: Request,
    roles: RoleManagementService = Depends(service),
) -> None:
    principal = getattr(request.state, "principal", None)
    if principal is not None and payload.actor_principal_id != principal.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authenticated principal cannot revoke roles as another user")
    try:
        roles.revoke(
            tenant_id=trusted_tenant(request),
            actor_principal_id=payload.actor_principal_id,
            assignment_id=assignment_id,
        )
    except RoleAuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
