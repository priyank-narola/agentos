import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    Tenant, Principal, PrincipalStatus, Agent, AgentStatus, Delegation, DelegationStatus,
    Tool, Action, CapabilityStatus, Resource, ResourceStatus, Policy, PolicyRule, PolicyEffect,
    ActionRequest, ActionRequestStatus, ApprovalRequest, ApprovalStatus, AuditEvent,
    FinancialExecution, ExecutionState, RiskClassification, Decision, DecisionType
)
from app.financial import compute_payload_digest


class ObservabilityService:
    """
    Enterprise Security Observability & Control Plane Service.
    Provides strictly READ-ONLY visibility into AgentOS security events, risk evaluations,
    policy decisions, identity posture, execution state, and audit integrity verification.
    Zero mutation capabilities. Strictly tenant-isolated.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_security_timeline(
        self, tenant_id: uuid.UUID, limit: int = 50, offset: int = 0, event_type: str | None = None
    ) -> dict[str, Any]:
        """Queries tenant-isolated audit event timeline."""
        stmt = select(AuditEvent).where(AuditEvent.tenant_id == tenant_id)
        if event_type:
            stmt = stmt.where(AuditEvent.event_type == event_type)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = self.db.scalar(count_stmt) or 0

        stmt = stmt.order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit)
        events = list(self.db.scalars(stmt).all())

        timeline_items = []
        for e in events:
            timeline_items.append({
                "id": str(e.id),
                "event_type": e.event_type,
                "actor_type": e.actor_type.value if hasattr(e.actor_type, "value") else str(e.actor_type),
                "actor_id": str(e.actor_id) if e.actor_id else None,
                "action_request_id": str(e.action_request_id) if e.action_request_id else None,
                "event_data": e.event_data,
                "created_at": e.created_at.isoformat() if e.created_at else None
            })

        return {
            "tenant_id": str(tenant_id),
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "events": timeline_items
        }

    def get_action_request_detail(self, tenant_id: uuid.UUID, request_id: uuid.UUID) -> dict[str, Any] | None:
        """Retrieves comprehensive security breakdown for a single ActionRequest within tenant scope."""
        stmt = (
            select(ActionRequest)
            .where(and_(ActionRequest.id == request_id, ActionRequest.tenant_id == tenant_id))
            .options(
                joinedload(ActionRequest.principal),
                joinedload(ActionRequest.agent),
                joinedload(ActionRequest.action).joinedload(Action.tool),
                joinedload(ActionRequest.resource),
                joinedload(ActionRequest.decisions),
                joinedload(ActionRequest.audit_events)
            )
        )
        req = self.db.scalar(stmt)
        if not req:
            return None

        # Fetch associated approval request if present
        approval_stmt = select(ApprovalRequest).where(ApprovalRequest.action_request_id == req.id)
        approval_req = self.db.scalar(approval_stmt)

        # Fetch financial execution record if present
        exec_stmt = select(FinancialExecution).where(FinancialExecution.action_request_id == req.id)
        exec_rec = self.db.scalar(exec_stmt)

        # Retrieve risk decision if present
        risk_event = next((e for e in req.audit_events if e.event_type == "RISK_EVALUATED"), None)
        risk_data = risk_event.event_data if risk_event else {}

        # Retrieve policy decision if present
        policy_decision = req.decisions[0] if req.decisions else None

        payload_digest = compute_payload_digest(req.parameters or {})

        return {
            "action_request_id": str(req.id),
            "tenant_id": str(req.tenant_id),
            "principal": {
                "id": str(req.principal.id) if req.principal else None,
                "name": req.principal.name if req.principal else None,
                "external_id": req.principal.external_id if req.principal else None
            },
            "agent": {
                "id": str(req.agent.id) if req.agent else None,
                "name": req.agent.name if req.agent else None,
                "purpose": req.agent.purpose if req.agent else None
            },
            "action": {
                "id": str(req.action.id) if req.action else None,
                "name": req.action.name if req.action else None,
                "tool": req.action.tool.name if (req.action and req.action.tool) else None
            },
            "resource": {
                "id": str(req.resource.id) if req.resource else None,
                "resource_type": req.resource.resource_type if req.resource else None,
                "resource_key": req.resource.resource_key if req.resource else None
            },
            "parameters": req.parameters,
            "payload_digest": payload_digest,
            "gateway_status": req.status.value if hasattr(req.status, "value") else str(req.status),
            "risk": {
                "score": risk_data.get("score") if isinstance(risk_data, dict) else None,
                "classification": risk_data.get("classification") if isinstance(risk_data, dict) else (req.action.risk_level.value if req.action else "UNKNOWN")
            },
            "policy": {
                "decision": policy_decision.decision.value if (policy_decision and hasattr(policy_decision.decision, "value")) else ("ALLOW" if policy_decision else "UNKNOWN"),
                "reason_code": (policy_decision.reason.partition(": ")[0] or policy_decision.reason) if policy_decision else None,
                "reason": (policy_decision.reason.partition(": ")[2] or policy_decision.reason) if policy_decision else None
            },
            "approval": {
                "required": approval_req is not None,
                "status": approval_req.status.value if (approval_req and hasattr(approval_req.status, "value")) else (approval_req.status if approval_req else None),
                "requested_by": str(approval_req.requested_by) if (approval_req and approval_req.requested_by) else None,
                "decided_by": str(approval_req.decided_by) if (approval_req and approval_req.decided_by) else None,
                "decided_at": approval_req.decided_at.isoformat() if (approval_req and approval_req.decided_at) else None
            },
            "execution": {
                "status": exec_rec.status.value if (exec_rec and hasattr(exec_rec.status, "value")) else (exec_rec.status if exec_rec else "NOT_EXECUTED"),
                "provider_transaction_id": exec_rec.provider_transaction_id if exec_rec else None,
                "provider_name": exec_rec.provider_name if exec_rec else None
            },
            "requested_at": req.requested_at.isoformat() if req.requested_at else None
        }

    def get_security_dashboard_metrics(self, tenant_id: uuid.UUID) -> dict[str, Any]:
        """Computes deterministic security control plane metrics for tenant_id."""
        total_requests = self.db.scalar(select(func.count(ActionRequest.id)).where(ActionRequest.tenant_id == tenant_id)) or 0
        pending_approvals = self.db.scalar(
            select(func.count(ApprovalRequest.id))
            .join(ActionRequest, ApprovalRequest.action_request_id == ActionRequest.id)
            .where(and_(ActionRequest.tenant_id == tenant_id, ApprovalRequest.status == ApprovalStatus.PENDING))
        ) or 0

        approved_executions = self.db.scalar(
            select(func.count(FinancialExecution.id))
            .where(and_(FinancialExecution.tenant_id == tenant_id, FinancialExecution.status == ExecutionState.SUCCEEDED))
        ) or 0


        rejected_actions = self.db.scalar(
            select(func.count(ActionRequest.id))
            .where(and_(ActionRequest.tenant_id == tenant_id, ActionRequest.status == ActionRequestStatus.REJECTED))
        ) or 0


        # Security event metrics from AuditEvents
        toctou_violations = self.db.scalar(
            select(func.count(AuditEvent.id))
            .where(and_(AuditEvent.tenant_id == tenant_id, AuditEvent.event_type.in_(["TOCTOU_VIOLATION", "TOCTOU_REVALIDATION_FAILED"])))
        ) or 0

        payload_tamper_attempts = self.db.scalar(
            select(func.count(AuditEvent.id))
            .where(and_(AuditEvent.tenant_id == tenant_id, AuditEvent.event_type == "PAYLOAD_TAMPER_DETECTED"))
        ) or 0

        auth_failures = self.db.scalar(
            select(func.count(AuditEvent.id))
            .where(and_(AuditEvent.tenant_id == tenant_id, AuditEvent.event_type == "AUTHENTICATION_FAILED"))
        ) or 0

        cross_tenant_attempts = self.db.scalar(
            select(func.count(AuditEvent.id))
            .where(and_(AuditEvent.tenant_id == tenant_id, AuditEvent.event_type == "CROSS_TENANT_ACCESS_DENIED"))
        ) or 0

        webhook_failures = self.db.scalar(
            select(func.count(AuditEvent.id))
            .where(and_(AuditEvent.tenant_id == tenant_id, AuditEvent.event_type == "WEBHOOK_FAILED"))
        ) or 0

        idempotency_conflicts = self.db.scalar(
            select(func.count(AuditEvent.id))
            .where(and_(AuditEvent.tenant_id == tenant_id, AuditEvent.event_type == "IDEMPOTENCY_CONFLICT"))
        ) or 0

        execution_failures = self.db.scalar(
            select(func.count(FinancialExecution.id))
            .where(and_(FinancialExecution.tenant_id == tenant_id, FinancialExecution.status.in_([ExecutionState.FAILED, ExecutionState.UNKNOWN])))
        ) or 0



        return {
            "tenant_id": str(tenant_id),
            "total_action_requests": total_requests,
            "pending_approvals": pending_approvals,
            "approved_executions": approved_executions,
            "rejected_actions": rejected_actions,
            "toctou_violations": toctou_violations,
            "payload_tampering_attempts": payload_tamper_attempts,
            "authentication_failures": auth_failures,
            "cross_tenant_attempts": cross_tenant_attempts,
            "webhook_failures": webhook_failures,
            "idempotency_conflicts": idempotency_conflicts,
            "execution_failures_timeouts": execution_failures
        }

    def get_risk_dashboard(self, tenant_id: uuid.UUID) -> dict[str, Any]:
        """Provides risk classification distribution and highest-risk action analytics."""
        requests = list(self.db.scalars(
            select(ActionRequest)
            .where(ActionRequest.tenant_id == tenant_id)
            .options(joinedload(ActionRequest.action), joinedload(ActionRequest.decisions))
        ).unique().all())

        risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        highest_risk_actions = []
        approval_required_actions = []
        rejected_high_risk_actions = []

        for req in requests:
            risk_level = req.action.risk_level.value if (req.action and req.action.risk_level) else "LOW"
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1

            if risk_level in ["HIGH", "CRITICAL"]:
                highest_risk_actions.append({"id": str(req.id), "action": req.action.name if req.action else None, "risk_level": risk_level, "requested_at": req.requested_at.isoformat() if req.requested_at else None})
                if req.status == ActionRequestStatus.REJECTED:
                    rejected_high_risk_actions.append({"id": str(req.id), "action": req.action.name if req.action else None, "risk_level": risk_level})

            if req.status == ActionRequestStatus.APPROVAL_PENDING:
                approval_required_actions.append({"id": str(req.id), "action": req.action.name if req.action else None, "risk_level": risk_level})

        return {
            "tenant_id": str(tenant_id),
            "risk_distribution": risk_counts,
            "highest_risk_actions": highest_risk_actions[:10],
            "approval_required_actions": approval_required_actions[:10],
            "rejected_high_risk_actions": rejected_high_risk_actions[:10]
        }

    def get_agent_security_posture(self, tenant_id: uuid.UUID, agent_id: uuid.UUID) -> dict[str, Any] | None:
        """Retrieves security posture and risk telemetry for a specific agent within tenant_id."""
        agent = self.db.scalar(
            select(Agent).where(and_(Agent.id == agent_id, Agent.tenant_id == tenant_id))
        )
        if not agent:
            return None

        # Fetch associated active delegations
        delegations = list(self.db.scalars(
            select(Delegation).where(and_(Delegation.agent_id == agent.id, Delegation.tenant_id == tenant_id, Delegation.status == DelegationStatus.ACTIVE))
        ).all())

        # Associated principals
        principal_ids = list(set([d.principal_id for d in delegations]))
        principals = list(self.db.scalars(
            select(Principal).where(and_(Principal.id.in_(principal_ids), Principal.tenant_id == tenant_id))
        ).all()) if principal_ids else []

        # Action volume telemetry
        recent_action_count = self.db.scalar(
            select(func.count(ActionRequest.id)).where(and_(ActionRequest.agent_id == agent.id, ActionRequest.tenant_id == tenant_id))
        ) or 0

        rejected_action_count = self.db.scalar(
            select(func.count(ActionRequest.id)).where(and_(ActionRequest.agent_id == agent.id, ActionRequest.tenant_id == tenant_id, ActionRequest.status == ActionRequestStatus.REJECTED))
        ) or 0

        violation_count = self.db.scalar(
            select(func.count(AuditEvent.id))
            .where(and_(
                AuditEvent.tenant_id == tenant_id,
                AuditEvent.actor_id == agent.id,
                AuditEvent.event_type.in_(["SECURITY_VIOLATION", "TOCTOU_VIOLATION", "PAYLOAD_TAMPER_DETECTED", "CROSS_TENANT_ACCESS_DENIED"])
            ))
        ) or 0

        last_activity = self.db.scalar(
            select(func.max(ActionRequest.requested_at)).where(and_(ActionRequest.agent_id == agent.id, ActionRequest.tenant_id == tenant_id))
        )

        return {
            "agent_id": str(agent.id),
            "tenant_id": str(agent.tenant_id),
            "name": agent.name,
            "status": agent.status.value if hasattr(agent.status, "value") else str(agent.status),
            "risk_classification": agent.risk_classification.value if hasattr(agent.risk_classification, "value") else str(agent.risk_classification),
            "owner_principal_id": str(agent.owner_principal_id),
            "associated_principals": [{"id": str(p.id), "name": p.name} for p in principals],
            "active_delegations": [{"id": str(d.id), "scope": d.scope} for d in delegations],
            "recent_action_count": recent_action_count,
            "rejected_action_count": rejected_action_count,
            "security_violation_count": violation_count,
            "last_activity": last_activity.isoformat() if last_activity else None
        }

    def get_tenant_security_posture(self, tenant_id: uuid.UUID) -> dict[str, Any]:
        """Provides tenant-wide security posture aggregates."""
        active_principals = self.db.scalar(
            select(func.count(Principal.id)).where(and_(Principal.tenant_id == tenant_id, Principal.status == PrincipalStatus.ACTIVE))
        ) or 0

        active_agents = self.db.scalar(
            select(func.count(Agent.id)).where(and_(Agent.tenant_id == tenant_id, Agent.status == AgentStatus.ACTIVE))
        ) or 0

        active_delegations = self.db.scalar(
            select(func.count(Delegation.id)).where(and_(Delegation.tenant_id == tenant_id, Delegation.status == DelegationStatus.ACTIVE))
        ) or 0

        action_volume = self.db.scalar(
            select(func.count(ActionRequest.id)).where(ActionRequest.tenant_id == tenant_id)
        ) or 0

        approval_volume = self.db.scalar(
            select(func.count(ApprovalRequest.id))
            .join(ActionRequest, ApprovalRequest.action_request_id == ActionRequest.id)
            .where(ActionRequest.tenant_id == tenant_id)
        ) or 0

        execution_volume = self.db.scalar(
            select(func.count(FinancialExecution.id)).where(FinancialExecution.tenant_id == tenant_id)
        ) or 0

        security_violations = self.db.scalar(
            select(func.count(AuditEvent.id))
            .where(and_(
                AuditEvent.tenant_id == tenant_id,
                AuditEvent.event_type.in_(["SECURITY_VIOLATION", "TOCTOU_VIOLATION", "PAYLOAD_TAMPER_DETECTED", "CROSS_TENANT_ACCESS_DENIED"])
            ))
        ) or 0

        high_risk_activity = self.db.scalar(
            select(func.count(ActionRequest.id))
            .join(Action, ActionRequest.action_id == Action.id)
            .where(and_(ActionRequest.tenant_id == tenant_id, Action.risk_level == RiskClassification.HIGH))
        ) or 0

        return {
            "tenant_id": str(tenant_id),
            "active_principals": active_principals,
            "active_agents": active_agents,
            "active_delegations": active_delegations,
            "action_volume": action_volume,
            "approval_volume": approval_volume,
            "execution_volume": execution_volume,
            "security_violations": security_violations,
            "high_risk_activity": high_risk_activity
        }

    def verify_audit_integrity(self, tenant_id: uuid.UUID) -> dict[str, Any]:
        """
        Runs comprehensive cryptographic and logical audit integrity verification.
        Detects 7 distinct security violations:
        1. MISSING_AUDIT_EVENT
        2. IMPOSSIBLE_EVENT_ORDERING
        3. CROSS_TENANT_CONTAMINATION
        4. EXECUTION_WITHOUT_APPROVAL
        5. APPROVAL_WITHOUT_VALID_REQUESTER (SoD Violation)
        6. EXECUTION_AFTER_REVOKED_DELEGATION
        7. PAYLOAD_DIGEST_MISMATCH
        """
        violations = []
        action_requests = list(self.db.scalars(
            select(ActionRequest)
            .where(ActionRequest.tenant_id == tenant_id)
            .options(
                joinedload(ActionRequest.audit_events),
                joinedload(ActionRequest.agent),
                joinedload(ActionRequest.principal),
                joinedload(ActionRequest.action)
            )
        ).unique().all())


        for req in action_requests:
            events = sorted(req.audit_events, key=lambda x: x.created_at if x.created_at else datetime.min.replace(tzinfo=timezone.utc))

            # 1. Check Missing Audit Event
            if not events:
                violations.append({
                    "type": "MISSING_AUDIT_EVENT",
                    "action_request_id": str(req.id),
                    "description": "ActionRequest exists with zero associated audit events."
                })

            # 2. Check Cross-Tenant Contamination
            for e in events:
                if e.tenant_id != tenant_id:
                    violations.append({
                        "type": "CROSS_TENANT_CONTAMINATION",
                        "action_request_id": str(req.id),
                        "audit_event_id": str(e.id),
                        "description": f"Audit event tenant {e.tenant_id} does not match request tenant {tenant_id}."
                    })

            # 3. Check Impossible Event Ordering
            event_types = [e.event_type for e in events]
            if "EXECUTION_SUCCEEDED" in event_types:
                exec_idx = event_types.index("EXECUTION_SUCCEEDED")
                if "ACTION_REQUEST_RECEIVED" in event_types:
                    recv_idx = event_types.index("ACTION_REQUEST_RECEIVED")
                    if exec_idx < recv_idx:
                        violations.append({
                            "type": "IMPOSSIBLE_EVENT_ORDERING",
                            "action_request_id": str(req.id),
                            "description": "EXECUTION_SUCCEEDED logged before ACTION_REQUEST_RECEIVED."
                        })

            # 4. Check Execution Without Approval
            exec_rec = self.db.scalar(select(FinancialExecution).where(FinancialExecution.action_request_id == req.id))
            approval_rec = self.db.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == req.id))

            if exec_rec and str(exec_rec.status) in ["SUCCEEDED", "EXECUTION_SUCCEEDED", "ExecutionState.SUCCEEDED"]:
                if req.action and str(req.action.risk_level) in ["HIGH", "CRITICAL", "RiskClassification.HIGH"]:
                    if not approval_rec or approval_rec.status != ApprovalStatus.APPROVED:

                        violations.append({
                            "type": "EXECUTION_WITHOUT_APPROVAL",
                            "action_request_id": str(req.id),
                            "description": "High-risk financial execution succeeded without valid human approval."
                        })

            # 5. Check Approval Without Valid Requester (SoD)
            if approval_rec and approval_rec.status == ApprovalStatus.APPROVED:
                if approval_rec.requested_by == approval_rec.decided_by:
                    violations.append({
                        "type": "APPROVAL_WITHOUT_VALID_REQUESTER",
                        "action_request_id": str(req.id),
                        "approval_id": str(approval_rec.id),
                        "description": "Separation of duties violation: Approver matches Requester."
                    })

            # 6. Check Execution After Revoked Delegation
            if exec_rec and str(exec_rec.status) in ["SUCCEEDED", "EXECUTION_SUCCEEDED", "ExecutionState.SUCCEEDED"]:
                delegation = self.db.scalar(
                    select(Delegation).where(and_(Delegation.principal_id == req.principal_id, Delegation.agent_id == req.agent_id))
                )
                if delegation and delegation.status == DelegationStatus.REVOKED:
                    violations.append({
                        "type": "EXECUTION_AFTER_REVOKED_DELEGATION",
                        "action_request_id": str(req.id),
                        "description": "Execution completed under a revoked delegation relationship."
                    })

            # 7. Check Payload Digest Mismatch
            expected_digest = compute_payload_digest(req.parameters or {})
            for e in events:
                if isinstance(e.event_data, dict) and "payload_digest" in e.event_data:
                    if e.event_data["payload_digest"] != expected_digest:
                        violations.append({
                            "type": "PAYLOAD_DIGEST_MISMATCH",
                            "action_request_id": str(req.id),
                            "audit_event_id": str(e.id),
                            "description": f"Audit digest {e.event_data['payload_digest']} does not match current request digest {expected_digest}."
                        })

        return {
            "tenant_id": str(tenant_id),
            "audit_integrity_status": "PASSED" if not violations else "VIOLATIONS_DETECTED",
            "total_requests_verified": len(action_requests),
            "violation_count": len(violations),
            "violations": violations
        }
