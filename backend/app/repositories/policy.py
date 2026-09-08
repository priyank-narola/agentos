from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import DEFAULT_TENANT_ID, Policy, PolicyRule
from app.repositories.registry import RegistryRepository


class PolicyRepository(RegistryRepository):
    def list_policies(self, tenant_id: UUID | None = None) -> list[Policy]:
        stmt = select(Policy).options(selectinload(Policy.rules)).order_by(Policy.priority, Policy.name, Policy.version)
        if tenant_id is not None:
            stmt = stmt.where(Policy.tenant_id == tenant_id)
        return list(self.db.scalars(stmt).unique().all())

    def get_policy(self, policy_id: UUID, tenant_id: UUID | None = None) -> Policy | None:
        stmt = select(Policy).options(selectinload(Policy.rules)).where(Policy.id == policy_id)
        if tenant_id is not None:
            stmt = stmt.where(Policy.tenant_id == tenant_id)
        return self.db.scalar(stmt)

    def list_active_policies(self, tenant_id: UUID | None = None) -> list[Policy]:
        """Active policies eligible for a request in ``tenant_id``.

        Tenant isolation: a tenant-owned policy is eligible only for its own
        tenant. Policies owned by the canonical DEFAULT tenant act as a shared
        baseline and are eligible everywhere (documented exception); this keeps
        legacy test data and demo seed behavior intact while never letting
        tenant B's tenant-owned policies apply to tenant A.
        """
        stmt = select(Policy).options(selectinload(Policy.rules)).where(Policy.status == "ACTIVE").order_by(Policy.priority, Policy.name, Policy.version)
        if tenant_id is not None:
            stmt = stmt.where(or_(Policy.tenant_id == tenant_id, Policy.tenant_id == DEFAULT_TENANT_ID))
        return list(self.db.scalars(stmt).unique().all())

    def get_rule(self, rule_id: UUID) -> PolicyRule | None:
        return self.db.get(PolicyRule, rule_id)
