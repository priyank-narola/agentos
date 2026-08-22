from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Policy, PolicyRule
from app.repositories.registry import RegistryRepository


class PolicyRepository(RegistryRepository):
    def list_policies(self) -> list[Policy]:
        return list(self.db.scalars(select(Policy).options(selectinload(Policy.rules)).order_by(Policy.priority, Policy.name, Policy.version)).unique().all())

    def get_policy(self, policy_id: UUID) -> Policy | None:
        return self.db.scalar(select(Policy).options(selectinload(Policy.rules)).where(Policy.id == policy_id))

    def list_active_policies(self) -> list[Policy]:
        return list(self.db.scalars(select(Policy).options(selectinload(Policy.rules)).where(Policy.status == "ACTIVE").order_by(Policy.priority, Policy.name, Policy.version)).unique().all())

    def get_rule(self, rule_id: UUID) -> PolicyRule | None:
        return self.db.get(PolicyRule, rule_id)
