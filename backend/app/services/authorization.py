"""Tenant role grants and authorization checks for consequential operations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import ActorType, AuditEvent, Principal, PrincipalRole, TenantRole


class RoleAuthorizationError(ValueError):
    """Raised when a principal lacks the required tenant-scoped product role."""


def grant_role(
    db: Session,
    *,
    tenant_id: UUID,
    principal_id: UUID,
    role: TenantRole,
    granted_by_principal_id: UUID | None = None,
) -> PrincipalRole:
    """Idempotently grant a role after verifying tenant ownership server-side."""
    principal = db.get(Principal, principal_id)
    if principal is None or principal.tenant_id != tenant_id:
        raise RoleAuthorizationError("Principal is not a member of this tenant")
    if granted_by_principal_id is not None:
        grantor = db.get(Principal, granted_by_principal_id)
        if grantor is None or grantor.tenant_id != tenant_id:
            raise RoleAuthorizationError("Granting principal is not a member of this tenant")
    existing = db.scalar(
        select(PrincipalRole).where(
            PrincipalRole.tenant_id == tenant_id,
            PrincipalRole.principal_id == principal_id,
            PrincipalRole.role == role,
        )
    )
    if existing is not None:
        return existing
    assignment = PrincipalRole(
        tenant_id=tenant_id,
        principal_id=principal_id,
        role=role,
        granted_by_principal_id=granted_by_principal_id,
    )
    db.add(assignment)
    db.flush()
    return assignment


def has_any_role(db: Session, *, tenant_id: UUID, principal_id: UUID, roles: set[TenantRole]) -> bool:
    """Return whether a principal has a role in the trusted tenant context."""
    return db.scalar(
        select(PrincipalRole.id).where(
            PrincipalRole.tenant_id == tenant_id,
            PrincipalRole.principal_id == principal_id,
            PrincipalRole.role.in_(roles),
        ).limit(1)
    ) is not None


def require_any_role(db: Session, *, tenant_id: UUID, principal_id: UUID, roles: set[TenantRole]) -> None:
    if not has_any_role(db, tenant_id=tenant_id, principal_id=principal_id, roles=roles):
        expected = ", ".join(sorted(role.value for role in roles))
        raise RoleAuthorizationError(f"Operator requires one of these tenant roles: {expected}")


class RoleManagementService:
    """Controlled role administration; bootstrap is deliberately not self-service."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, tenant_id: UUID) -> list[PrincipalRole]:
        return list(
            self.db.scalars(
                select(PrincipalRole)
                .where(PrincipalRole.tenant_id == tenant_id)
                .order_by(PrincipalRole.principal_id, PrincipalRole.role)
            ).all()
        )

    def grant(self, *, tenant_id: UUID, actor_principal_id: UUID, principal_id: UUID, role: TenantRole) -> PrincipalRole:
        require_any_role(
            self.db,
            tenant_id=tenant_id,
            principal_id=actor_principal_id,
            roles={TenantRole.ADMIN},
        )
        already_granted = has_any_role(
            self.db,
            tenant_id=tenant_id,
            principal_id=principal_id,
            roles={role},
        )
        assignment = grant_role(
            self.db,
            tenant_id=tenant_id,
            principal_id=principal_id,
            role=role,
            granted_by_principal_id=actor_principal_id,
        )
        if not already_granted:
            self.db.add(AuditEvent(
                tenant_id=tenant_id,
                event_type="TENANT_ROLE_GRANTED",
                actor_type=ActorType.PRINCIPAL,
                actor_id=actor_principal_id,
                event_data={"assignment_id": str(assignment.id), "principal_id": str(principal_id), "role": role.value},
            ))
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def revoke(self, *, tenant_id: UUID, actor_principal_id: UUID, assignment_id: UUID) -> None:
        """Revoke a role without permitting a tenant to lose its last admin."""
        require_any_role(
            self.db,
            tenant_id=tenant_id,
            principal_id=actor_principal_id,
            roles={TenantRole.ADMIN},
        )
        assignment = self.db.get(PrincipalRole, assignment_id)
        if assignment is None or assignment.tenant_id != tenant_id:
            raise RoleAuthorizationError("Role assignment was not found in this tenant")
        if assignment.role == TenantRole.ADMIN:
            admin_count = self.db.scalar(
                select(func.count(PrincipalRole.id)).where(
                    PrincipalRole.tenant_id == tenant_id,
                    PrincipalRole.role == TenantRole.ADMIN,
                )
            ) or 0
            if admin_count <= 1:
                raise RoleAuthorizationError("Cannot revoke the last tenant ADMIN role")
        self.db.add(AuditEvent(
            tenant_id=tenant_id,
            event_type="TENANT_ROLE_REVOKED",
            actor_type=ActorType.PRINCIPAL,
            actor_id=actor_principal_id,
            event_data={"assignment_id": str(assignment.id), "principal_id": str(assignment.principal_id), "role": assignment.role.value},
        ))
        self.db.delete(assignment)
        self.db.commit()
