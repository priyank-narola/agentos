from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Action, ActionRequest, Agent, Delegation, Policy, PolicyRule, Principal, Resource, Tool
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
        return self.repository.save(Policy(**data))

    def list_policies(self, tenant_id: UUID | None = None) -> list[Policy]:
        return self.repository.list_policies(tenant_id=tenant_id)

    def get_policy(self, policy_id: UUID, tenant_id: UUID | None = None) -> Policy | None:
        return self.repository.get_policy(policy_id, tenant_id=tenant_id)

    def create_rule(self, policy_id: UUID, payload: PolicyRuleCreate, tenant_id: UUID | None = None) -> PolicyRule | None:
        if self.get_policy(policy_id, tenant_id=tenant_id) is None:
            return None
        return self.repository.save(PolicyRule(policy_id=policy_id, **payload.model_dump()))

    def evaluate(self, payload: PolicyEvaluationRequest, tenant_id: UUID | None = None):
        principal = self.db.get(Principal, payload.principal_id)
        agent = self.db.get(Agent, payload.agent_id)
        tool = self.db.get(Tool, payload.tool_id)
        action = self.db.get(Action, payload.action_id)
        resource = self.db.get(Resource, payload.resource_id)
        if action is not None and tool is not None and action.tool_id != tool.id:
            action = None
        delegations = list(self.db.scalars(select(Delegation).where(Delegation.agent_id == payload.agent_id, Delegation.principal_id == payload.principal_id)).all())
        policies = self.repository.list_active_policies(tenant_id=tenant_id)
        request = EvaluationInput(principal_id=payload.principal_id, agent_id=payload.agent_id, tool_id=payload.tool_id, action_id=payload.action_id, resource_id=payload.resource_id, parameters=payload.parameters, policy_context=payload.policy_context, evaluated_at=payload.evaluated_at or datetime.now(timezone.utc))
        return self.evaluator.evaluate(request, ResolvedRecords(principal=principal, agent=agent, tool=tool, action=action, resource=resource, delegations=delegations, policies=policies))
