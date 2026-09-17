"""Coherent governance ACTIVITY for the default demo tenant.

``seed_demo`` (see ``app/seed.py``) provisions the *static catalog* — principals,
agents, tools, actions, resources, delegations, policies — but no live activity.
Without activity, the control-plane surfaces that visualise the governance chain
(Action Governance, Approvals, Observability / Audit / Proof) are empty for the
default tenant that the local development UI resolves to.

This module fills that gap the only correct way: by driving the **real**
``GatewayService`` and ``ApprovalService`` end-to-end. Every row it produces is
therefore coherent *by construction* and mirrors exactly what a live request
would create — a BLOCK never carries an execution, an approved action executes
via the sandbox provider, a rejected or still-pending one never does. It is both
demo data and a functional end-to-end exercise of the pipeline.

It is fully idempotent: gateway submissions use stable idempotency keys (so a
re-run returns the existing request rather than duplicating it), and approval
transitions are guarded on current status. Zero real money movement — execution
is always the in-process ``SandboxPaymentProvider``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    DEFAULT_TENANT_ID,
    Action,
    ActionRequest,
    Agent,
    ApprovalRequest,
    ApprovalStatus,
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
    TenantRole,
    Resource,
    ResourceSensitivity,
    ResourceStatus,
    RiskClassification,
    Tool,
)
from app.schemas import ApprovalActionRequest, GatewayRequestCreate
from app.services.approval import ApprovalConflictError, ApprovalService
from app.services.execution_ledger import fetch_execution_status
from app.services.authorization import grant_role
from app.services.gateway import GatewayIdempotencyConflict, GatewayService

logger = logging.getLogger(__name__)

# Stable identifiers so the activity layer is idempotent across re-seeds.
APPROVER_EXTERNAL_ID = "demo-approver"
DEMO_ACCOUNT_KEY = "ACC-DEMO-TREASURY-01"


def _default(session: Session, model, **filters):
    """First matching row scoped to the default tenant (or global when tenant is NULL)."""
    return session.scalar(select(model).filter_by(**filters))


def _ensure_approver(session: Session, requester: Principal) -> Principal:
    """A second ACTIVE human principal so approvals satisfy separation of duties."""
    approver = session.scalar(
        select(Principal).where(
            Principal.tenant_id == DEFAULT_TENANT_ID,
            Principal.external_id == APPROVER_EXTERNAL_ID,
        )
    )
    if approver is None:
        approver = Principal(
            tenant_id=DEFAULT_TENANT_ID,
            name="Dana Reviewer",
            type=PrincipalType.HUMAN,
            external_id=APPROVER_EXTERNAL_ID,
            status=PrincipalStatus.ACTIVE,
        )
        session.add(approver)
        session.flush()
    grant_role(session, tenant_id=DEFAULT_TENANT_ID, principal_id=approver.id, role=TenantRole.APPROVER)
    grant_role(session, tenant_id=DEFAULT_TENANT_ID, principal_id=approver.id, role=TenantRole.OPERATOR)
    return approver


def _ensure_wire_capability(session: Session, requester: Principal, finance_agent: Agent) -> tuple[Action, Resource]:
    """Provision an idempotent ``wire_transfer`` capability in the default tenant.

    ``wire_transfer`` is the one action the execution engine settles through the
    sandbox provider, so it is what exercises the approve -> revalidate -> execute
    path. Mirrors the flagship treasury environment but inside the default tenant.
    """
    payments = _default(session, Tool, name="Payments")
    if payments is None:
        payments = Tool(name="Payments", description="Payment operations", status=CapabilityStatus.ACTIVE)
        session.add(payments)
        session.flush()

    action = session.scalar(
        select(Action).where(Action.tool_id == payments.id, Action.name == "wire_transfer")
    )
    if action is None:
        action = Action(
            tenant_id=DEFAULT_TENANT_ID,
            tool=payments,
            name="wire_transfer",
            description="Outbound corporate wire transfer",
            risk_level=RiskClassification.HIGH,
            status=CapabilityStatus.ACTIVE,
        )
        session.add(action)
        session.flush()

    resource = session.scalar(
        select(Resource).where(
            Resource.tenant_id == DEFAULT_TENANT_ID,
            Resource.resource_type == "account",
            Resource.resource_key == DEMO_ACCOUNT_KEY,
        )
    )
    if resource is None:
        resource = Resource(
            tenant_id=DEFAULT_TENANT_ID,
            resource_type="account",
            resource_key=DEMO_ACCOUNT_KEY,
            sensitivity=ResourceSensitivity.HIGH,
            status=ResourceStatus.ACTIVE,
        )
        session.add(resource)
        session.flush()

    policy = _default(session, Policy, name="Demo Wire Transfer Policy", version=1)
    if policy is None:
        policy = Policy(
            tenant_id=DEFAULT_TENANT_ID,
            name="Demo Wire Transfer Policy",
            version=1,
            priority=5,
            status=PolicyStatus.ACTIVE,
            description="Authorizes treasury wire transfers subject to human approval on elevated risk",
        )
        policy.rules = [
            PolicyRule(effect=PolicyEffect.ALLOW, action="wire_transfer", resource_type="account", priority=5, conditions=None)
        ]
        session.add(policy)
        session.flush()

    # Delegation binding the requester to the finance agent for wire transfers.
    delegation = session.scalar(
        select(Delegation).where(
            Delegation.principal_id == requester.id,
            Delegation.agent_id == finance_agent.id,
            Delegation.tenant_id == DEFAULT_TENANT_ID,
            Delegation.scope == "wire_transfer",
        )
    )
    if delegation is None:
        session.add(
            Delegation(
                tenant_id=DEFAULT_TENANT_ID,
                principal=requester,
                agent=finance_agent,
                scope="wire_transfer",
                status=DelegationStatus.ACTIVE,
                issued_at=datetime.now(timezone.utc),
            )
        )
        session.flush()

    session.commit()
    return action, resource


def _wire_params(amount: str, reference: str) -> dict:
    return {
        "amount": amount,
        "currency": "USD",
        "beneficiary_id": "BEN-DEMO-VENDOR-01",
        "source_account_id": DEMO_ACCOUNT_KEY,
        "destination_account_id": "ACC-VENDOR-4471",
        "transaction_reference": reference,
        "purpose": "Vendor settlement (sandbox demo)",
    }


def seed_default_tenant_activity(session: Session) -> dict:
    """Drive the real gateway/approval pipeline to produce a coherent activity spread.

    Idempotent. Returns a coherence report: for every flow, the deterministic
    decision and the authoritative execution status, so the caller can assert
    (a BLOCK must never be EXECUTED, etc.).
    """
    requester = session.scalar(
        select(Principal).where(
            Principal.tenant_id == DEFAULT_TENANT_ID,
            Principal.external_id == "demo-admin",
        )
    )
    if requester is None:
        logger.warning("seed_default_tenant_activity: default tenant not seeded; run seed_demo first")
        return {"flows": [], "skipped": "default catalog missing"}

    approver = _ensure_approver(session, requester)
    finance_agent = _default(session, Agent, name="FinanceAgent")
    sales_agent = _default(session, Agent, name="SalesAgent")
    research_agent = _default(session, Agent, name="ResearchAgent")

    wire_action, wire_resource = _ensure_wire_capability(session, requester, finance_agent)

    read_action = session.scalar(select(Action).where(Action.name == "read_customer"))
    crm_resource = _default(session, Resource, resource_type="crm_record")
    payroll_action = session.scalar(select(Action).where(Action.name == "read_sensitive_payroll"))
    payroll_resource = _default(session, Resource, resource_type="dataset")

    gateway = GatewayService(session)
    approvals = ApprovalService(session)

    # (agent, action, resource, params, idempotency_key, post_decision_action)
    flows = [
        (sales_agent, read_action, crm_resource, {"customer_id": "CUST-1001", "fields": ["name", "email"]}, "demo-act-read-customer", None),
        (research_agent, payroll_action, payroll_resource, {"dataset": "payroll_2026_q3", "row_limit": 250}, "demo-act-read-payroll", None),
        (finance_agent, wire_action, wire_resource, _wire_params("25000.00", "REF-DEMO-APPROVED-01"), "demo-act-wire-approved", "approve"),
        (finance_agent, wire_action, wire_resource, _wire_params("8200.00", "REF-DEMO-REJECTED-01"), "demo-act-wire-rejected", "reject"),
        (finance_agent, wire_action, wire_resource, _wire_params("15400.00", "REF-DEMO-PENDING-01"), "demo-act-wire-pending", None),
    ]

    report = []
    for agent, action, resource, params, idem_key, post in flows:
        if agent is None or action is None or resource is None:
            report.append({"idempotency_key": idem_key, "skipped": "missing catalog record"})
            continue

        try:
            res = gateway.submit(
                GatewayRequestCreate(
                    principal_id=requester.id,
                    agent_id=agent.id,
                    action_id=action.id,
                    resource_id=resource.id,
                    parameters=params,
                    idempotency_key=idem_key,
                )
            )
        except GatewayIdempotencyConflict as exc:
            report.append({"idempotency_key": idem_key, "error": str(exc)})
            continue

        request_id = res.action_request_id
        decision = res.decision

        # Post-decision human action (only meaningful when approval was required).
        if post in {"approve", "reject"}:
            approval = session.scalar(
                select(ApprovalRequest).where(ApprovalRequest.action_request_id == request_id)
            )
            if approval is not None and approval.status == ApprovalStatus.PENDING:
                try:
                    payload = ApprovalActionRequest(approver_principal_id=approver.id)
                    if post == "approve":
                        approvals.approve(approval.id, payload)
                    else:
                        approvals.reject(approval.id, payload)
                except ApprovalConflictError as exc:
                    logger.info("Approval transition skipped for %s: %s", idem_key, exc)

        report.append({
            "idempotency_key": idem_key,
            "action": action.name,
            "decision": decision,
            "approval_required": res.approval_required,
            "post_action": post,
            "execution_status": fetch_execution_status(session, request_id),
        })

    return {"tenant_id": str(DEFAULT_TENANT_ID), "flows": report}


if __name__ == "__main__":
    from app.db.session import SessionLocal

    if SessionLocal is None:
        raise SystemExit("DATABASE_URL must be configured before seeding activity")
    with SessionLocal() as db:
        import json

        print(json.dumps(seed_default_tenant_activity(db), indent=2, default=str))
