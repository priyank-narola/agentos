"""Tenant role grants and sensitive operator authorization tests."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Principal, PrincipalStatus, PrincipalType, Tenant, TenantRole
from app.services.authorization import RoleAuthorizationError, RoleManagementService, grant_role, has_any_role
from app.config import Settings
import app.api.authorization as api_authorization
from app.api.authorization import require_tenant_roles


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def reset_db():
    with Session() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()


def test_admin_grants_tenant_role_without_cross_tenant_escape():
    with Session() as db:
        tenant = Tenant(id=uuid.uuid4(), name="Acme", slug="acme")
        other_tenant = Tenant(id=uuid.uuid4(), name="Elsewhere", slug="elsewhere")
        admin = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Admin", external_id="admin", status=PrincipalStatus.ACTIVE)
        operator = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Operator", external_id="operator", status=PrincipalStatus.ACTIVE)
        outsider = Principal(id=uuid.uuid4(), tenant_id=other_tenant.id, type=PrincipalType.HUMAN, name="Outsider", external_id="outsider", status=PrincipalStatus.ACTIVE)
        db.add_all([tenant, other_tenant, admin, operator, outsider])
        db.flush()
        grant_role(db, tenant_id=tenant.id, principal_id=admin.id, role=TenantRole.ADMIN)
        db.commit()

        assignment = RoleManagementService(db).grant(
            tenant_id=tenant.id,
            actor_principal_id=admin.id,
            principal_id=operator.id,
            role=TenantRole.OPERATOR,
        )
        assert assignment.role == TenantRole.OPERATOR
        assert has_any_role(db, tenant_id=tenant.id, principal_id=operator.id, roles={TenantRole.OPERATOR})

        with pytest.raises(RoleAuthorizationError, match="not a member"):
            RoleManagementService(db).grant(
                tenant_id=tenant.id,
                actor_principal_id=admin.id,
                principal_id=outsider.id,
                role=TenantRole.OPERATOR,
            )


def test_non_admin_cannot_grant_role():
    with Session() as db:
        tenant = Tenant(id=uuid.uuid4(), name="Acme", slug="acme")
        user = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="User", external_id="user", status=PrincipalStatus.ACTIVE)
        target = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Target", external_id="target", status=PrincipalStatus.ACTIVE)
        db.add_all([tenant, user, target])
        db.commit()
        with pytest.raises(RoleAuthorizationError, match="ADMIN"):
            RoleManagementService(db).grant(
                tenant_id=tenant.id,
                actor_principal_id=user.id,
                principal_id=target.id,
                role=TenantRole.OPERATOR,
            )


def test_admin_can_revoke_role_but_not_the_last_admin():
    with Session() as db:
        tenant = Tenant(id=uuid.uuid4(), name="Acme", slug="acme")
        admin = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Admin", external_id="admin", status=PrincipalStatus.ACTIVE)
        second_admin = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Second", external_id="second", status=PrincipalStatus.ACTIVE)
        operator = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Operator", external_id="operator", status=PrincipalStatus.ACTIVE)
        db.add_all([tenant, admin, second_admin, operator])
        db.flush()
        first_admin_assignment = grant_role(db, tenant_id=tenant.id, principal_id=admin.id, role=TenantRole.ADMIN)
        second_admin_assignment = grant_role(db, tenant_id=tenant.id, principal_id=second_admin.id, role=TenantRole.ADMIN)
        operator_assignment = grant_role(db, tenant_id=tenant.id, principal_id=operator.id, role=TenantRole.OPERATOR)
        db.commit()

        roles = RoleManagementService(db)
        roles.revoke(tenant_id=tenant.id, actor_principal_id=admin.id, assignment_id=operator_assignment.id)
        assert not has_any_role(db, tenant_id=tenant.id, principal_id=operator.id, roles={TenantRole.OPERATOR})
        roles.revoke(tenant_id=tenant.id, actor_principal_id=admin.id, assignment_id=second_admin_assignment.id)
        with pytest.raises(RoleAuthorizationError, match="last tenant ADMIN"):
            roles.revoke(tenant_id=tenant.id, actor_principal_id=admin.id, assignment_id=first_admin_assignment.id)


def test_staging_role_dependency_fails_closed_then_allows_granted_role(monkeypatch):
    """Route-level gates must not silently become authenticated-user-only gates."""
    from types import SimpleNamespace

    with Session() as db:
        tenant = Tenant(id=uuid.uuid4(), name="Acme", slug="acme")
        auditor = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Auditor", external_id="auditor", status=PrincipalStatus.ACTIVE)
        db.add_all([tenant, auditor])
        db.commit()
        request = SimpleNamespace(state=SimpleNamespace(principal=auditor, tenant_id=tenant.id))
        monkeypatch.setattr(api_authorization, "settings", Settings(app_env="staging"))
        dependency = require_tenant_roles({TenantRole.AUDITOR})

        with pytest.raises(HTTPException) as error:
            dependency(request, db)
        assert error.value.status_code == 403

        grant_role(db, tenant_id=tenant.id, principal_id=auditor.id, role=TenantRole.AUDITOR)
        db.commit()
        dependency(request, db)


def test_reconciliation_inbox_requires_operator_or_admin_role_outside_development(monkeypatch):
    """A tenant member must not browse uncertain provider outcomes by default."""
    from types import SimpleNamespace
    import app.api.authorization as reconciliation_authorization
    from app.api.reconciliation import operator_required

    with Session() as db:
        tenant = Tenant(id=uuid.uuid4(), name="Acme", slug="reconciliation-acme")
        member = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Member", external_id="member", status=PrincipalStatus.ACTIVE)
        db.add_all([tenant, member])
        db.commit()
        request = SimpleNamespace(state=SimpleNamespace(principal=member, tenant_id=tenant.id))
        monkeypatch.setattr(reconciliation_authorization, "settings", Settings(app_env="staging"))

        with pytest.raises(HTTPException) as error:
            operator_required(request, db)
        assert error.value.status_code == 403

        grant_role(db, tenant_id=tenant.id, principal_id=member.id, role=TenantRole.OPERATOR)
        db.commit()
        operator_required(request, db)


def test_agent_registry_mutations_require_operator_or_admin_outside_development(monkeypatch):
    """An authenticated tenant member cannot silently alter agent authority."""
    from types import SimpleNamespace

    import app.api.authorization as registry_authorization
    from app.api.registry import registry_writer_required

    with Session() as db:
        tenant = Tenant(id=uuid.uuid4(), name="Acme", slug="agent-registry-acme")
        member = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Member", external_id="agent-registry-member", status=PrincipalStatus.ACTIVE)
        db.add_all([tenant, member])
        db.commit()
        request = SimpleNamespace(state=SimpleNamespace(principal=member, tenant_id=tenant.id))
        monkeypatch.setattr(registry_authorization, "settings", Settings(app_env="staging"))

        with pytest.raises(HTTPException) as error:
            registry_writer_required(request, db)
        assert error.value.status_code == 403

        grant_role(db, tenant_id=tenant.id, principal_id=member.id, role=TenantRole.OPERATOR)
        db.commit()
        registry_writer_required(request, db)
