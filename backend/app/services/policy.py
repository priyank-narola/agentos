from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import ActorType, Action, Agent, AuditEvent, Delegation, Policy, PolicyRule, PolicyStatus, Principal, Resource, Tool
from app.policy import DeterministicPolicyEvaluator, EvaluationInput, ResolvedRecords
from app.repositories.policy import PolicyRepository
from app.schemas import PolicyCreate, PolicyEvaluationRequest, PolicyRuleCreate
from app.services.errors import RegistryConflictError, RegistryValidationError


class PolicyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = PolicyRepository(db)
        self.evaluator = DeterministicPolicyEvaluator()

    def create_policy(self, payload: PolicyCreate, tenant_id: UUID | None = None) -> Policy:
        data = payload.model_dump()
        if tenant_id is not None:
            data["tenant_id"] = tenant_id
        latest_version = self.repository.latest_version(payload.name, tenant_id=tenant_id)
        expected_version = (latest_version or 0) + 1
        if payload.version != expected_version:
            raise RegistryValidationError(
                f"Policy version must be {expected_version} for {payload.name!r}; use a new draft version rather than overwriting history"
            )
        return self.repository.save(Policy(**data))

    def list_policies(self, tenant_id: UUID | None = None) -> list[Policy]:
        return self.repository.list_policies(tenant_id=tenant_id)

    def get_policy(self, policy_id: UUID, tenant_id: UUID | None = None) -> Policy | None:
        return self.repository.get_policy(policy_id, tenant_id=tenant_id)

    def create_rule(self, policy_id: UUID, payload: PolicyRuleCreate, tenant_id: UUID | None = None) -> PolicyRule | None:
        policy = self.get_policy(policy_id, tenant_id=tenant_id)
        if policy is None:
            return None
        self._require_draft(policy, "Rules can only be changed on a draft policy version")
        return self.repository.save(PolicyRule(policy_id=policy_id, **payload.model_dump()))

    def delete_rule(self, policy_id: UUID, rule_id: UUID, tenant_id: UUID | None = None) -> bool | None:
        policy = self.get_policy(policy_id, tenant_id=tenant_id)
        if policy is None:
            return None
        self._require_draft(policy, "Rules can only be changed on a draft policy version")
        rule = next((item for item in policy.rules if item.id == rule_id), None)
        if rule is None:
            return False
        self.db.delete(rule)
        self.db.commit()
        return True

    def create_next_version(self, policy_id: UUID, tenant_id: UUID | None = None, actor_id: UUID | None = None) -> Policy | None:
        source = self.repository.get_policy_for_update(policy_id, tenant_id=tenant_id)
        if source is None:
            return None
        latest_version = self.repository.latest_version(source.name, tenant_id=tenant_id)
        draft = Policy(
            tenant_id=source.tenant_id,
            name=source.name,
            description=source.description,
            status=PolicyStatus.DRAFT,
            version=(latest_version or 0) + 1,
            priority=source.priority,
        )
        self.db.add(draft)
        self.db.flush()
        for rule in source.rules:
            self.db.add(PolicyRule(
                policy_id=draft.id,
                effect=rule.effect,
                action=rule.action,
                resource_type=rule.resource_type,
                conditions=rule.conditions,
                priority=rule.priority,
            ))
        self._audit("POLICY_VERSION_DRAFTED", draft, actor_id, {"source_policy_id": str(source.id), "source_version": source.version})
        self._commit_or_conflict()
        self.db.refresh(draft)
        return draft

    def publish_policy(self, policy_id: UUID, tenant_id: UUID | None = None, actor_id: UUID | None = None) -> Policy | None:
        policy = self.repository.get_policy_for_update(policy_id, tenant_id=tenant_id)
        if policy is None:
            return None
        self._require_draft(policy, "Only a draft policy version can be published")
        if not policy.rules:
            raise RegistryValidationError("A policy needs at least one rule before it can be published")
        # At most one active version of a named policy may govern a tenant.
        # Publishing the reviewed replacement retires the previous live version
        # in the same transaction, preventing ambiguous parallel versions.
        superseded = self.repository.active_versions_for_update(policy.name, tenant_id=tenant_id)
        for active in superseded:
            active.status = PolicyStatus.RETIRED
            self._audit("POLICY_RETIRED", active, actor_id, {"reason": "superseded", "superseded_by_policy_id": str(policy.id), "superseded_by_version": policy.version})
        policy.status = PolicyStatus.ACTIVE
        self._audit("POLICY_PUBLISHED", policy, actor_id, {"rule_count": len(policy.rules), "superseded_policy_ids": [str(item.id) for item in superseded]})
        self._commit_or_conflict()
        self.db.refresh(policy)
        return policy

    def retire_policy(self, policy_id: UUID, tenant_id: UUID | None = None, actor_id: UUID | None = None) -> Policy | None:
        policy = self.repository.get_policy_for_update(policy_id, tenant_id=tenant_id)
        if policy is None:
            return None
        if policy.status == PolicyStatus.RETIRED:
            raise RegistryValidationError("This policy version is already retired")
        policy.status = PolicyStatus.RETIRED
        self._audit("POLICY_RETIRED", policy, actor_id, {"reason": "manual_retirement"})
        self._commit_or_conflict()
        self.db.refresh(policy)
        return policy

    @staticmethod
    def _require_draft(policy: Policy, message: str) -> None:
        if policy.status != PolicyStatus.DRAFT:
            raise RegistryValidationError(message)

    def _audit(self, event_type: str, policy: Policy, actor_id: UUID | None, event_data: dict) -> None:
        self.db.add(AuditEvent(
            tenant_id=policy.tenant_id,
            event_type=event_type,
            actor_type=ActorType.PRINCIPAL if actor_id else ActorType.SYSTEM,
            actor_id=actor_id,
            event_data={"policy_id": str(policy.id), "policy_name": policy.name, "policy_version": policy.version, **event_data},
        ))

    def _commit_or_conflict(self) -> None:
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise RegistryConflictError("Policy lifecycle update conflicted with another change; refresh and try again") from error

    def evaluate(self, payload: PolicyEvaluationRequest, tenant_id: UUID | None = None):
        return self._evaluate(payload, self.repository.list_active_policies(tenant_id=tenant_id))

    def simulate_draft(self, policy_id: UUID, payload: PolicyEvaluationRequest, tenant_id: UUID | None = None):
        """Evaluate exactly one draft policy without persisting an action or changing live policy."""
        policy = self.get_policy(policy_id, tenant_id=tenant_id)
        if policy is None:
            return None
        self._require_draft(policy, "Only an unpublished draft can be simulated")
        return self._evaluate(payload, [policy], include_non_active_policies=True)

    def _evaluate(self, payload: PolicyEvaluationRequest, policies: list[Policy], *, include_non_active_policies: bool = False):
        principal = self.db.get(Principal, payload.principal_id)
        agent = self.db.get(Agent, payload.agent_id)
        tool = self.db.get(Tool, payload.tool_id)
        action = self.db.get(Action, payload.action_id)
        resource = self.db.get(Resource, payload.resource_id)
        if action is not None and tool is not None and action.tool_id != tool.id:
            action = None
        delegations = list(self.db.scalars(select(Delegation).where(Delegation.agent_id == payload.agent_id, Delegation.principal_id == payload.principal_id)).all())
        request = EvaluationInput(principal_id=payload.principal_id, agent_id=payload.agent_id, tool_id=payload.tool_id, action_id=payload.action_id, resource_id=payload.resource_id, parameters=payload.parameters, policy_context=payload.policy_context, evaluated_at=payload.evaluated_at or datetime.now(timezone.utc))
        return self.evaluator.evaluate(request, ResolvedRecords(principal=principal, agent=agent, tool=tool, action=action, resource=resource, delegations=delegations, policies=policies), include_non_active_policies=include_non_active_policies)
