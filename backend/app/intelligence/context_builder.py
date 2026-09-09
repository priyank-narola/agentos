"""Context Builder — constructs ActionContext from server-side state only.

Never trusts client-supplied identity, risk, or tenant data. All history is
derived from real ActionRequest/AuditEvent records.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Action, ActionRequest, ActionRequestStatus, Agent, AuditEvent, Delegation,
    Principal, Resource, Tool,
)
from app.intelligence.models import ActionContext


def build_action_context(
    db: Session,
    agent: Agent,
    principal: Principal,
    action: Action,
    tool: Tool,
    resource: Resource,
    parameters: dict[str, Any],
    tenant_id: Any,
) -> ActionContext:
    """Build an ActionContext from authoritative server-side records."""
    # Behavioral history from real action requests
    prior_requests = list(db.scalars(
        select(ActionRequest).where(
            ActionRequest.agent_id == agent.id,
            ActionRequest.tenant_id == tenant_id,
        )
    ).all())

    prior_actions_count = len(prior_requests)
    # Get decision reasons for failure detection
    from app.db.models import Decision
    decision_reasons = []
    for r in prior_requests:
        d = db.scalar(select(Decision).where(Decision.action_request_id == r.id).order_by(Decision.decided_at.desc()).limit(1))
        if d and d.reason:
            decision_reasons.append(d.reason.lower())
    prior_failures = sum(1 for reason in decision_reasons if "failed" in reason)
    prior_blocked = sum(1 for r in prior_requests if r.status == ActionRequestStatus.REJECTED)
    prior_tamper = db.scalar(
        select(func.count(AuditEvent.id)).where(
            AuditEvent.tenant_id == tenant_id,
            AuditEvent.event_type.in_(["SECURITY_PAYLOAD_TAMPERED", "APPROVAL_EXPIRED"]),
        )
    ) or 0
    prior_cross_tenant = db.scalar(
        select(func.count(AuditEvent.id)).where(
            AuditEvent.tenant_id == tenant_id,
            AuditEvent.event_type == "CROSS_TENANT_ACCESS_DENIED",
        )
    ) or 0
    prior_approval_rejections = db.scalar(
        select(func.count(AuditEvent.id)).where(
            AuditEvent.tenant_id == tenant_id,
            AuditEvent.event_type == "APPROVAL_REJECTED",
        )
    ) or 0

    # Delegation scope
    delegation = db.scalar(
        select(Delegation).where(
            Delegation.agent_id == agent.id,
            Delegation.principal_id == principal.id,
            Delegation.tenant_id == tenant_id,
        )
    )
    delegation_scope = delegation.scope if delegation else "none"

    # Time pattern
    now = datetime.now(timezone.utc)
    outside_normal_hours = now.hour < 6 or now.hour >= 22

    return ActionContext(
        action_name=action.name,
        action_risk_level=action.risk_level.value if hasattr(action.risk_level, "value") else str(action.risk_level),
        tool_name=tool.name,
        resource_type=resource.resource_type,
        resource_key=resource.resource_key,
        resource_sensitivity=resource.sensitivity.value if hasattr(resource.sensitivity, "value") else str(resource.sensitivity),
        agent_name=agent.name,
        agent_risk_classification=agent.risk_classification.value if hasattr(agent.risk_classification, "value") else str(agent.risk_classification),
        agent_id=str(agent.id),
        principal_id=str(principal.id),
        tenant_id=str(tenant_id),
        delegation_scope=delegation_scope,
        parameters=parameters,
        prior_actions_count=prior_actions_count,
        prior_failures=prior_failures,
        prior_blocked=prior_blocked,
        prior_tamper_attempts=prior_tamper,
        prior_cross_tenant_attempts=prior_cross_tenant,
        prior_approval_rejections=prior_approval_rejections,
        is_first_action_for_agent=prior_actions_count == 0,
        outside_normal_hours=outside_normal_hours,
    )
