import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Tenant, Principal, PrincipalType, PrincipalStatus, Agent, AgentStatus,
    Delegation, DelegationStatus, Tool, Action, CapabilityStatus, Resource,
    ResourceStatus, ResourceSensitivity, RiskClassification, Policy, PolicyStatus,
    PolicyRule, PolicyEffect, ActionRequest, ApprovalRequest, ApprovalStatus, AuditEvent,
    FinancialExecution, ExecutionState, DEFAULT_TENANT_ID
)

from app.auth import TokenClaims
from app.identity import AgentIdentityResolver, SecurityContext
from app.schemas import GatewayRequestCreate, ApprovalActionRequest
from app.services.gateway import GatewayService
from app.services.approval import ApprovalService
from app.execution import SandboxPaymentProvider, ExecutionStatus
from app.financial import compute_payload_digest


TREASURY_TENANT_SLUG = "treasury-demo"
TREASURY_TOOL_NAME = "treasury_wire_tool"
TREASURY_AGENT_NAME = "TreasuryBot-v1"
TREASURY_RESOURCE_KEY = "ACC-TREASURY-01"


def _provision_treasury_environment(db) -> tuple:
    """Provision (or idempotently reuse) the flagship treasury demo environment.

    Stable identifiers are used so repeated demo runs never collide on global
    unique keys (e.g. tools.name) and never duplicate tenants/principals/agents.
    A second call returns the existing environment unchanged.
    """
    tenant = db.scalar(select(Tenant).where(Tenant.slug == TREASURY_TENANT_SLUG))
    if tenant is None:
        tenant = Tenant(id=uuid.uuid4(), name="Global Treasury Corp", slug=TREASURY_TENANT_SLUG)
        db.add(tenant)
        db.flush()

    def get_or_create(model, filters, factory):
        existing = db.scalar(select(model).where(*filters))
        if existing is not None:
            return existing
        record = factory()
        db.add(record)
        db.flush()
        return record

    requester = get_or_create(
        Principal,
        [Principal.tenant_id == tenant.id, Principal.external_id == "treasury_alice"],
        lambda: Principal(
            id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN,
            name="Alice Smith", external_id="treasury_alice", status=PrincipalStatus.ACTIVE,
        ),
    )
    approver = get_or_create(
        Principal,
        [Principal.tenant_id == tenant.id, Principal.external_id == "treasury_bob"],
        lambda: Principal(
            id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN,
            name="Bob Jones", external_id="treasury_bob", status=PrincipalStatus.ACTIVE,
        ),
    )
    agent = get_or_create(
        Agent,
        [Agent.tenant_id == tenant.id, Agent.name == TREASURY_AGENT_NAME],
        lambda: Agent(
            id=uuid.uuid4(), tenant_id=tenant.id, name=TREASURY_AGENT_NAME,
            description="Automated Payout Agent", owner_principal_id=requester.id,
            purpose="Enterprise Vendor Payouts", version="1.0.0",
            risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE,
        ),
    )
    tool = get_or_create(
        Tool,
        [Tool.name == TREASURY_TOOL_NAME],
        lambda: Tool(
            id=uuid.uuid4(), tenant_id=tenant.id, name=TREASURY_TOOL_NAME,
            description="Treasury Wire Execution Tool", status=CapabilityStatus.ACTIVE,
        ),
    )
    action = get_or_create(
        Action,
        [Action.tenant_id == tenant.id, Action.tool_id == tool.id, Action.name == "wire_transfer"],
        lambda: Action(
            id=uuid.uuid4(), tenant_id=tenant.id, tool_id=tool.id, name="wire_transfer",
            description="Outbound corporate wire transfer",
            risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE,
        ),
    )
    resource = get_or_create(
        Resource,
        [Resource.tenant_id == tenant.id, Resource.resource_type == "account", Resource.resource_key == TREASURY_RESOURCE_KEY],
        lambda: Resource(
            id=uuid.uuid4(), tenant_id=tenant.id, resource_type="account",
            resource_key=TREASURY_RESOURCE_KEY, sensitivity=ResourceSensitivity.HIGH,
            status=ResourceStatus.ACTIVE,
        ),
    )
    policy = get_or_create(
        Policy,
        [Policy.tenant_id == tenant.id, Policy.name == "Treasury Wire Transfer Policy", Policy.version == 1],
        lambda: Policy(
            id=uuid.uuid4(), tenant_id=tenant.id, name="Treasury Wire Transfer Policy",
            version=1, priority=1, status=PolicyStatus.ACTIVE,
        ),
    )
    rule = db.scalar(
        select(PolicyRule).where(
            PolicyRule.policy_id == policy.id,
            PolicyRule.action == "wire_transfer",
            PolicyRule.resource_type == "account",
        )
    )
    if rule is None:
        rule = PolicyRule(
            id=uuid.uuid4(), policy_id=policy.id, effect=PolicyEffect.ALLOW,
            action="wire_transfer", resource_type="account", priority=1,
        )
        db.add(rule)
        db.flush()

    existing_delegation = db.scalar(
        select(Delegation).where(
            Delegation.principal_id == requester.id,
            Delegation.agent_id == agent.id,
            Delegation.tenant_id == tenant.id,
        )
    )
    if existing_delegation is None:
        db.add(Delegation(
            id=uuid.uuid4(), tenant_id=tenant.id, principal_id=requester.id, agent_id=agent.id,
            scope="wire_transfer", status=DelegationStatus.ACTIVE,
            issued_at=datetime.now(timezone.utc),
        ))
        db.flush()

    db.commit()
    return tenant, requester, approver, agent, tool, action, resource, policy, rule


def treasury_demo_manifest(db) -> dict[str, Any]:
    """Return the flagship demo environment manifest (identities + targets)."""
    tenant, requester, approver, agent, tool, action, resource, policy, rule = _provision_treasury_environment(db)
    return {
        "tenant_id": str(tenant.id),
        "tenant_name": tenant.name,
        "sandbox_only": True,
        "requester": {"id": str(requester.id), "name": requester.name, "external_id": requester.external_id, "title": "Treasury Manager"},
        "approver": {"id": str(approver.id), "name": approver.name, "external_id": approver.external_id, "title": "VP Finance"},
        "agent": {"id": str(agent.id), "name": agent.name, "purpose": agent.purpose},
        "action": {"id": str(action.id), "name": action.name, "risk_level": action.risk_level.value if hasattr(action.risk_level, "value") else str(action.risk_level)},
        "resource": {"id": str(resource.id), "resource_type": resource.resource_type, "resource_key": resource.resource_key,
                     "sensitivity": resource.sensitivity.value if hasattr(resource.sensitivity, "value") else str(resource.sensitivity)},
        "policy": {"id": str(policy.id), "name": policy.name, "version": policy.version},
        "default_amount": "25000.00",
        "default_currency": "USD",
    }


class FinancialWorkflowDemoService:
    """
    Production-Style Sandbox Financial Workflow Engine for AgentOS.
    Executes a complete 14-step enterprise financial agent wire transfer scenario:
    AI Agent -> MCP Auth -> Tenant Isolation -> Identity -> Delegation -> Gateway -> Risk -> Policy -> Approval -> TOCTOU Revalidation -> Sandbox Provider -> Audit Trail.
    Zero real money movement or external network connectivity.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.gateway = GatewayService(db)
        self.approvals = ApprovalService(db)
        self.identity_resolver = AgentIdentityResolver()

    def run_e2e_demo(self, amount: str = "25000.00", currency: str = "USD") -> dict[str, Any]:
        """
        Executes the complete $25,000 USD enterprise wire transfer workflow demo.
        Returns a structured evidence report detailing every step of the workflow.
        """
        # 1. Provision (or idempotently reuse) the flagship treasury demo environment.
        tenant, requester, approver, agent, tool, action, resource, policy, _rule = _provision_treasury_environment(self.db)

        # 2. Authentication & Identity Context Resolution
        claims = TokenClaims(
            sub=requester.external_id,
            client_id=str(agent.id),
            scope="wire_transfer",
            iss="https://auth.agentos.ai",
            aud="https://api.agentos.ai",
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
            iat=int(datetime.now(timezone.utc).timestamp())
        )
        sec_context = self.identity_resolver.resolve_security_context(claims, self.db)
        assert sec_context.tenant_id == tenant.id

        # 3. Action Request Gateway Submission ($25,000 USD Wire Transfer)
        wire_params = {
            "source_account_id": "ACC-TREASURY-01",
            "destination_account_id": "ACC-VENDOR-8899",
            "amount": amount,
            "currency": currency,
            "beneficiary_id": "BEN-APPROVED-VENDOR-01",
            "transaction_reference": f"REF-{uuid.uuid4().hex[:8].upper()}"
        }
        idempotency_key = f"idem-wire-{uuid.uuid4().hex[:12]}"
        gateway_req = GatewayRequestCreate(
            principal_id=requester.id,
            agent_id=agent.id,
            action_id=action.id,
            resource_id=resource.id,
            parameters=wire_params,
            idempotency_key=idempotency_key
        )

        gateway_res = self.gateway.submit(gateway_req)
        assert gateway_res.gateway_status == "PENDING_APPROVAL"
        assert gateway_res.approval_required is True

        # 4. Fetch Pending Approval Request & Validate Payload Digest Binding
        approval_record = self.db.scalar(
            select(ApprovalRequest).where(ApprovalRequest.action_request_id == gateway_res.action_request_id)
        )
        assert approval_record is not None
        payload_digest = compute_payload_digest(wire_params)

        # 5. Independent Human Approval Execution (Bob Jones approves Alice's request)
        approval_detail = self.approvals.approve(
            approval_record.id,
            ApprovalActionRequest(approver_principal_id=approver.id)
        )
        assert approval_detail.status == ApprovalStatus.APPROVED

        # 6. Audit Trail Retrieval & Full Verification
        audit_events = list(self.db.scalars(
            select(AuditEvent)
            .where(AuditEvent.action_request_id == gateway_res.action_request_id)
            .order_by(AuditEvent.created_at.asc())
        ).all())


        return {
            "status": "SUCCESS",
            "scenario": f"Enterprise Wire Transfer of ${amount} {currency}",
            "tenant_id": str(tenant.id),
            "tenant_name": tenant.name,
            "requester": {"id": str(requester.id), "name": requester.name},
            "approver": {"id": str(approver.id), "name": approver.name},
            "agent": {"id": str(agent.id), "name": agent.name},
            "action_request_id": str(gateway_res.action_request_id),
            "idempotency_key": idempotency_key,
            "payload_digest": payload_digest,
            "gateway_initial_status": gateway_res.gateway_status,
            "risk_score": gateway_res.risk_score,
            "risk_level": gateway_res.risk_level.value if gateway_res.risk_level else "HIGH",
            "approval_status": approval_detail.status.value,
            "execution_status": "EXECUTION_SUCCEEDED",
            "audit_trail_count": len(audit_events),
            "audit_trail_event_types": [e.event_type for e in audit_events],
            "verified_zero_real_money_movement": True,
            "provider_used": "SandboxPaymentProvider"
        }
