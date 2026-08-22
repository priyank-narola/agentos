from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.db.models import (
    Action,
    Agent,
    AgentStatus,
    CapabilityStatus,
    Delegation,
    DelegationStatus,
    Policy,
    PolicyEffect,
    PolicyRule,
    PolicyStatus,
    Principal,
    PrincipalStatus,
    PrincipalType,
    Resource,
    ResourceSensitivity,
    ResourceStatus,
    RiskClassification,
    Tool,
)
from app.policy import DeterministicPolicyEvaluator, EvaluationInput, ReasonCode, ResolvedRecords


NOW = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)


def scenario(*, delegation_scope="read_customer", delegation_status=DelegationStatus.ACTIVE, expires_at=None, agent_status=AgentStatus.ACTIVE, action_status=CapabilityStatus.ACTIVE, resource_status=ResourceStatus.ACTIVE, risk=RiskClassification.LOW, rules=None, policy_status=PolicyStatus.ACTIVE):
    principal_id, agent_id, tool_id, action_id, resource_id = uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
    principal = Principal(id=principal_id, type=PrincipalType.HUMAN, name="Owner", external_id=str(uuid4()), status=PrincipalStatus.ACTIVE)
    agent = Agent(id=agent_id, name="SalesAgent", owner_principal_id=principal_id, purpose="Sales", version="1.0.0", status=agent_status, risk_classification=RiskClassification.MEDIUM)
    tool = Tool(id=tool_id, name="CRM", description="CRM", status=CapabilityStatus.ACTIVE)
    action = Action(id=action_id, tool_id=tool.id, name="read_customer", description="Read customer", risk_level=risk, status=action_status)
    resource = Resource(id=resource_id, resource_type="crm_record", resource_key="customer-001", sensitivity=ResourceSensitivity.MEDIUM, status=resource_status)
    delegation = Delegation(id=uuid4(), principal_id=principal_id, agent_id=agent_id, scope=delegation_scope, status=delegation_status, issued_at=NOW - timedelta(hours=1), expires_at=expires_at)
    policies = []
    for effect, priority, policy_priority in rules or []:
        policy = Policy(id=uuid4(), name=f"Policy-{uuid4()}", version=1, priority=policy_priority, status=policy_status)
        policy.rules = [PolicyRule(id=uuid4(), policy=policy, effect=effect, action="read_customer", resource_type="crm_record", priority=priority)]
        policies.append(policy)
    request = EvaluationInput(principal_id, agent_id, tool.id, action_id, resource_id, {}, {}, NOW)
    records = ResolvedRecords(principal, agent, tool, action, resource, [delegation], policies)
    return request, records


def evaluate(**kwargs):
    request, records = scenario(**kwargs)
    return DeterministicPolicyEvaluator().evaluate(request, records)


def test_valid_delegated_low_risk_action_allows() -> None:
    result = evaluate(rules=[(PolicyEffect.ALLOW, 10, 10)])
    assert (result.decision, result.reason_code) == ("ALLOW", ReasonCode.POLICY_ALLOW)


def test_missing_delegation_denies() -> None:
    request, records = scenario(rules=[(PolicyEffect.ALLOW, 10, 10)])
    records = ResolvedRecords(records.principal, records.agent, records.tool, records.action, records.resource, [], records.policies)
    result = DeterministicPolicyEvaluator().evaluate(request, records)
    assert result.reason_code == ReasonCode.DELEGATION_MISSING


def test_expired_delegation_denies() -> None:
    result = evaluate(expires_at=NOW - timedelta(minutes=1), rules=[(PolicyEffect.ALLOW, 10, 10)])
    assert result.reason_code == ReasonCode.DELEGATION_EXPIRED


def test_suspended_agent_denies() -> None:
    result = evaluate(agent_status=AgentStatus.SUSPENDED, rules=[(PolicyEffect.ALLOW, 10, 10)])
    assert result.reason_code == ReasonCode.AGENT_INACTIVE


def test_disabled_action_denies() -> None:
    result = evaluate(action_status=CapabilityStatus.DISABLED, rules=[(PolicyEffect.ALLOW, 10, 10)])
    assert result.reason_code == ReasonCode.ACTION_INACTIVE


def test_restricted_resource_denies() -> None:
    result = evaluate(resource_status=ResourceStatus.RESTRICTED, rules=[(PolicyEffect.ALLOW, 10, 10)])
    assert result.reason_code == ReasonCode.RESOURCE_INACTIVE


def test_explicit_deny_takes_precedence_over_allow() -> None:
    result = evaluate(rules=[(PolicyEffect.ALLOW, 1, 1), (PolicyEffect.DENY, 99, 99)])
    assert result.reason_code == ReasonCode.POLICY_DENY
    assert result.decision == "DENY"


def test_policy_priority_orders_matching_rules() -> None:
    result = evaluate(rules=[(PolicyEffect.ALLOW, 10, 20), (PolicyEffect.DENY, 10, 10)])
    assert result.matched_policies[0].policy_priority == 10
    assert result.reason_code == ReasonCode.POLICY_DENY


def test_high_risk_allow_requires_approval() -> None:
    result = evaluate(risk=RiskClassification.HIGH, rules=[(PolicyEffect.ALLOW, 10, 10)])
    assert result.decision == "REQUIRE_APPROVAL"
    assert result.reason_code == ReasonCode.HIGH_RISK_APPROVAL
    assert result.approval_required is True


def test_no_matching_rule_is_default_deny() -> None:
    result = evaluate(rules=[])
    assert (result.decision, result.reason_code) == ("DENY", ReasonCode.DEFAULT_DENY)


def test_invalid_identity_relationship_denies() -> None:
    request, records = scenario(rules=[(PolicyEffect.ALLOW, 10, 10)])
    records.agent.owner_principal_id = uuid4()
    result = DeterministicPolicyEvaluator().evaluate(request, records)
    assert result.reason_code == ReasonCode.PRINCIPAL_AGENT_MISMATCH


def test_invalid_reference_denies() -> None:
    request, records = scenario(rules=[(PolicyEffect.ALLOW, 10, 10)])
    records = ResolvedRecords(records.principal, records.agent, records.tool, None, records.resource, records.delegations, records.policies)
    result = DeterministicPolicyEvaluator().evaluate(request, records)
    assert result.reason_code == ReasonCode.INVALID_REFERENCE


def test_scope_mismatch_denies() -> None:
    result = evaluate(delegation_scope="finance.transfer", rules=[(PolicyEffect.ALLOW, 10, 10)])
    assert result.reason_code == ReasonCode.DELEGATION_SCOPE_MISMATCH


def test_repeated_evaluation_is_identical() -> None:
    request, records = scenario(rules=[(PolicyEffect.ALLOW, 10, 10)])
    evaluator = DeterministicPolicyEvaluator()
    first = evaluator.evaluate(request, records).model_dump(mode="json")
    second = evaluator.evaluate(request, records).model_dump(mode="json")
    assert first == second
