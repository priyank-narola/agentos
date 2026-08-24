from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.db.models import (
    Action,
    Agent,
    AgentStatus,
    CapabilityStatus,
    Delegation,
    DelegationStatus,
    Policy,
    PolicyEffect,
    Resource,
    ResourceStatus,
    RiskClassification,
    Tool,
)
from app.schemas import EvaluationTraceStep, MatchedPolicyRule, PolicyEvaluationResult


@dataclass(frozen=True)
class EvaluationInput:
    principal_id: Any
    agent_id: Any
    tool_id: Any
    action_id: Any
    resource_id: Any
    parameters: dict[str, Any]
    policy_context: dict[str, Any]
    evaluated_at: datetime
    risk_score: int | None = None
    risk_classification: str | None = None


class ReasonCode:
    INVALID_REFERENCE = "INVALID_REFERENCE"
    PRINCIPAL_AGENT_MISMATCH = "PRINCIPAL_AGENT_MISMATCH"
    AGENT_INACTIVE = "AGENT_INACTIVE"
    DELEGATION_MISSING = "DELEGATION_MISSING"
    DELEGATION_INACTIVE = "DELEGATION_INACTIVE"
    DELEGATION_EXPIRED = "DELEGATION_EXPIRED"
    DELEGATION_SCOPE_MISMATCH = "DELEGATION_SCOPE_MISMATCH"
    TOOL_INACTIVE = "TOOL_INACTIVE"
    ACTION_INACTIVE = "ACTION_INACTIVE"
    RESOURCE_INACTIVE = "RESOURCE_INACTIVE"
    POLICY_DENY = "POLICY_DENY"
    POLICY_ALLOW = "POLICY_ALLOW"
    HIGH_RISK_APPROVAL = "HIGH_RISK_APPROVAL"
    DEFAULT_DENY = "DEFAULT_DENY"


@dataclass(frozen=True)
class ResolvedRecords:
    principal: Any
    agent: Agent
    tool: Tool
    action: Action
    resource: Resource
    delegations: list[Delegation]
    policies: list[Policy]


class DeterministicPolicyEvaluator:
    """Pure policy decision component. It never persists or executes an action."""

    def evaluate(self, request: EvaluationInput, records: ResolvedRecords) -> PolicyEvaluationResult:
        trace: list[EvaluationTraceStep] = []

        def add(code: str, outcome: str, detail: str) -> None:
            trace.append(EvaluationTraceStep(step=len(trace) + 1, code=code, outcome=outcome, detail=detail))

        if records.principal is None or records.agent is None or records.tool is None or records.action is None or records.resource is None:
            add(ReasonCode.INVALID_REFERENCE, "DENY", "One or more referenced records could not be resolved")
            return self._result("DENY", ReasonCode.INVALID_REFERENCE, "Referenced identity, capability, or resource does not exist", trace, records)
        if records.agent.owner_principal_id != records.principal.id:
            add(ReasonCode.PRINCIPAL_AGENT_MISMATCH, "DENY", "The principal is not the registered owner of the agent")
            return self._result("DENY", ReasonCode.PRINCIPAL_AGENT_MISMATCH, "Principal and agent identity relationship is invalid", trace, records)
        add("IDENTITY_VALID", "PASS", "Principal and agent ownership relationship is valid")
        if records.agent.status != AgentStatus.ACTIVE:
            add(ReasonCode.AGENT_INACTIVE, "DENY", f"Agent status is {records.agent.status.value}")
            return self._result("DENY", ReasonCode.AGENT_INACTIVE, "Agent is not active", trace, records)
        add("AGENT_ACTIVE", "PASS", "Agent is active")

        matching_delegations = [d for d in records.delegations if d.principal_id == request.principal_id and d.agent_id == request.agent_id]
        if not matching_delegations:
            add(ReasonCode.DELEGATION_MISSING, "DENY", "No delegation exists from this principal to this agent")
            return self._result("DENY", ReasonCode.DELEGATION_MISSING, "Delegated authority is missing", trace, records)
        valid_delegations = []
        for delegation in matching_delegations:
            if delegation.status == DelegationStatus.REVOKED:
                continue
            if delegation.status == DelegationStatus.EXPIRED or (delegation.expires_at is not None and delegation.expires_at <= request.evaluated_at):
                continue
            valid_delegations.append(delegation)
        if not valid_delegations:
            code = ReasonCode.DELEGATION_EXPIRED if any(d.expires_at and d.expires_at <= request.evaluated_at or d.status == DelegationStatus.EXPIRED for d in matching_delegations) else ReasonCode.DELEGATION_INACTIVE
            add(code, "DENY", "No active, non-expired delegation is available")
            return self._result("DENY", code, "Delegated authority is not currently valid", trace, records)
        operation = records.action.name.split("_", 1)[0]
        required_scope = f"{records.tool.name.lower()}.{operation}"
        scoped = [d for d in valid_delegations if d.scope in {required_scope, records.action.name, "*"} or d.scope.endswith(f".{operation}")]
        if not scoped:
            add(ReasonCode.DELEGATION_SCOPE_MISMATCH, "DENY", f"Required scope {required_scope} was not delegated")
            return self._result("DENY", ReasonCode.DELEGATION_SCOPE_MISMATCH, "Delegated scope does not cover this action", trace, records)
        add("DELEGATION_VALID", "PASS", f"Active delegation covers scope {required_scope}")

        if records.tool.status != CapabilityStatus.ACTIVE:
            add(ReasonCode.TOOL_INACTIVE, "DENY", f"Tool status is {records.tool.status.value}")
            return self._result("DENY", ReasonCode.TOOL_INACTIVE, "Tool is not active", trace, records)
        if records.action.status != CapabilityStatus.ACTIVE:
            add(ReasonCode.ACTION_INACTIVE, "DENY", f"Action status is {records.action.status.value}")
            return self._result("DENY", ReasonCode.ACTION_INACTIVE, "Action is not active", trace, records)
        if records.resource.status != ResourceStatus.ACTIVE:
            add(ReasonCode.RESOURCE_INACTIVE, "DENY", f"Resource status is {records.resource.status.value}")
            return self._result("DENY", ReasonCode.RESOURCE_INACTIVE, "Resource is restricted or retired", trace, records)
        add("CAPABILITIES_ACTIVE", "PASS", "Tool, action, and resource are active")

        matched = self._matched_rules(records, request)
        add("POLICY_RULES_RESOLVED", "PASS" if matched else "EMPTY", f"Resolved {len(matched)} matching active policy rules")
        if matched:
            deny = next((rule for rule in matched if rule.rule_effect == PolicyEffect.DENY), None)
            if deny:
                add(ReasonCode.POLICY_DENY, "DENY", f"Explicit deny from {deny.policy_name} v{deny.policy_version}")
                return self._result("DENY", ReasonCode.POLICY_DENY, "An explicit deny policy rule takes precedence", trace, records, matched)
            add(ReasonCode.POLICY_ALLOW, "PASS", f"Allow rule selected from {matched[0].policy_name} v{matched[0].policy_version}")
            if records.action.risk_level == RiskClassification.HIGH:
                add(ReasonCode.HIGH_RISK_APPROVAL, "REQUIRE_APPROVAL", "High-risk action requires human approval before execution")
                return self._result("REQUIRE_APPROVAL", ReasonCode.HIGH_RISK_APPROVAL, "Policy allows the action but its high risk requires approval", trace, records, matched, approval=True)
            return self._result("ALLOW", ReasonCode.POLICY_ALLOW, "A matching allow policy rule authorizes the action", trace, records, matched)
        add(ReasonCode.DEFAULT_DENY, "DENY", "No matching allow policy rule was found")
        return self._result("DENY", ReasonCode.DEFAULT_DENY, "No policy rule authorizes this action", trace, records)

    def _matched_rules(self, records: ResolvedRecords, request: EvaluationInput) -> list[MatchedPolicyRule]:
        matched = []
        for policy in records.policies:
            if policy.status.value != "ACTIVE":
                continue
            for rule in policy.rules:
                if rule.action != records.action.name or rule.resource_type != records.resource.resource_type:
                    continue
                if not self._conditions_match(rule.conditions or {}, request.parameters, request.policy_context, records.resource):
                    continue
                matched.append(MatchedPolicyRule(policy_id=policy.id, policy_name=policy.name, policy_version=policy.version, policy_priority=policy.priority, rule_id=rule.id, rule_effect=rule.effect, rule_priority=rule.priority, conditions=rule.conditions))
        return sorted(matched, key=lambda item: (item.policy_priority, item.rule_priority, str(item.policy_id), str(item.rule_id)))

    @staticmethod
    def _conditions_match(conditions: dict[str, Any], parameters: dict[str, Any], context: dict[str, Any], resource: Resource) -> bool:
        for key, expected in conditions.items():
            if key == "resource_sensitivity" and resource.sensitivity.value != expected:
                return False
            if key == "amount_lte":
                amount = parameters.get("amount")
                if not isinstance(amount, (int, float)) or amount > expected:
                    return False
            if key == "context" and context.get("name") != expected:
                return False
            if key not in {"resource_sensitivity", "amount_lte", "context"}:
                return False
        return True

    @staticmethod
    def _result(decision, code, reason, trace, records, matched=None, approval=False):
        return PolicyEvaluationResult(decision=decision, reason_code=code, reason=reason, matched_policies=matched or [], risk_level=records.action.risk_level if records.action else None, delegation_status=DelegationStatus.ACTIVE if records.delegations else None, approval_required=approval, trace=trace)
