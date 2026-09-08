"""Treasury demo environment idempotency + SoD-eligible approver tests.

Proves the flagship demo environment can be initialized repeatedly without
colliding on global-unique keys, that the requester can never appear as an
eligible approver (separation of duties preserved), that an independent
approver completes the sandboxed wire, and that the full financial workflow is
repeatable on the same database.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.db.models import Tenant, Principal, Agent, Tool, ApprovalRequest, FinancialExecution, ExecutionState, Delegation
from app.main import app
from app.services.demo import treasury_demo_manifest, FinancialWorkflowDemoService, _provision_treasury_environment
from app.services.approval import ApprovalService
from app.schemas import GatewayRequestCreate, ApprovalActionRequest


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    with TestingSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    with TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture
def db_session():
    with TestingSession() as session:
        yield session


def _manifest(db: Session):
    return treasury_demo_manifest(db)


def test_treasury_demo_manifest_is_idempotent(db_session):
    """Manifest/bootstrap creates the environment once and reuses it thereafter."""
    first = _manifest(db_session)
    second = _manifest(db_session)

    assert first["tenant_name"] == "Global Treasury Corp"
    assert first["requester"]["name"] == "Alice Smith"
    assert first["approver"]["name"] == "Bob Jones"
    assert first["agent"]["name"] == "TreasuryBot-v1"
    assert first["action"]["name"] == "wire_transfer"
    assert first["resource"]["resource_key"] == "ACC-TREASURY-01"
    # Reuse, never duplicate.
    assert second["tenant_id"] == first["tenant_id"]
    assert second["requester"]["id"] == first["requester"]["id"]
    assert second["approver"]["id"] == first["approver"]["id"]
    assert second["agent"]["id"] == first["agent"]["id"]
    assert second["action"]["id"] == first["action"]["id"]
    assert second["resource"]["id"] == first["resource"]["id"]

    tenants = db_session.scalar(select(func.count(Tenant.id)).where(Tenant.slug == "treasury-demo"))
    assert tenants == 1
    tools = db_session.scalar(select(func.count(Tool.id)).where(Tool.name == "treasury_wire_tool"))
    assert tools == 1
    principals = db_session.scalar(select(func.count(Principal.id)).where(Principal.tenant_id == uuid.UUID(first["tenant_id"])))
    assert principals == 2


def test_financial_workflow_demo_is_repeatable(db_session):
    """The flagship e2e demo runs twice on the same DB without collisions."""
    first_run = FinancialWorkflowDemoService(db_session).run_e2e_demo(amount="25000.00", currency="USD")
    second_run = FinancialWorkflowDemoService(db_session).run_e2e_demo(amount="25000.00", currency="USD")
    assert first_run["status"] == "SUCCESS"
    assert second_run["status"] == "SUCCESS"
    assert first_run["tenant_id"] == second_run["tenant_id"]
    tenants = db_session.scalar(select(func.count(Tenant.id)).where(Tenant.slug == "treasury-demo"))
    assert tenants == 1
    tools = db_session.scalar(select(func.count(Tool.id)).where(Tool.name == "treasury_wire_tool"))
    assert tools == 1
    # Each run created its own action request + one SUCCEEDED ledger row.
    executions = db_session.scalar(select(func.count(FinancialExecution.id)).where(FinancialExecution.status == ExecutionState.SUCCEEDED))
    assert executions == 2


def test_requester_never_eligible_approver_and_independent_approver_succeeds(db_session):
    """SoD: Alice (requester) is excluded from eligible approvers; Bob approves."""
    manifest = _manifest(db_session)

    # A high-risk wire requires human approval.
    gateway_req = GatewayRequestCreate(
        principal_id=manifest["requester"]["id"],
        agent_id=manifest["agent"]["id"],
        action_id=manifest["action"]["id"],
        resource_id=manifest["resource"]["id"],
        parameters={
            "source_account_id": "ACC-TREASURY-01",
            "destination_account_id": "ACC-VENDOR-1",
            "amount": "25000.00",
            "currency": "USD",
            "beneficiary_id": "BEN-1",
            "transaction_reference": f"REF-{uuid.uuid4().hex[:8].upper()}",
        },
        idempotency_key=f"idem-treasury-{uuid.uuid4()}",
    )
    from app.services.gateway import GatewayService
    res = GatewayService(db_session).submit(gateway_req)
    assert res.gateway_status == "PENDING_APPROVAL"
    assert res.approval_required is True

    approval = db_session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == res.action_request_id))
    service = ApprovalService(db_session)
    eligible = service.eligible_approvers(approval.id)
    approver_ids = [item["id"] for item in eligible]
    assert manifest["requester"]["id"] not in approver_ids
    assert manifest["approver"]["id"] in approver_ids

    # Distinct independent approver (Bob) succeeds end-to-end.
    detail = service.approve(approval.id, ApprovalActionRequest(approver_principal_id=manifest["approver"]["id"]))
    assert detail.status.value == "APPROVED"
    ledger = db_session.scalar(select(FinancialExecution).where(FinancialExecution.action_request_id == res.action_request_id))
    assert ledger is not None
    assert ledger.status == ExecutionState.SUCCEEDED
    assert str(ledger.tenant_id) == manifest["tenant_id"]

    # Requester self-approval remains rejected (invariant not weakened).
    from app.services.approval import ApprovalConflictError
    with pytest.raises(ApprovalConflictError):
        service.approve(approval.id, ApprovalActionRequest(approver_principal_id=manifest["requester"]["id"]))


def test_eligible_approvers_endpoint_returns_same_tenant_only(db_session):
    """The approvers route returns same-tenant ACTIVE humans, never the requester."""
    manifest = _manifest(db_session)
    # A principal from another tenant must never appear as an eligible approver.
    other = Tenant(id=uuid.uuid4(), name="Other Corp", slug=f"other-{uuid.uuid4().hex[:6]}")
    other_bob = Principal(id=uuid.uuid4(), tenant_id=other.id, type=__import__("app.db.models", fromlist=["PrincipalType"]).PrincipalType.HUMAN, name="Other Approver", external_id="other_bob", status=__import__("app.db.models", fromlist=["PrincipalStatus"]).PrincipalStatus.ACTIVE)
    db_session.add_all([other, other_bob])
    db_session.commit()

    from app.services.gateway import GatewayService
    res = GatewayService(db_session).submit(GatewayRequestCreate(
        principal_id=manifest["requester"]["id"],
        agent_id=manifest["agent"]["id"],
        action_id=manifest["action"]["id"],
        resource_id=manifest["resource"]["id"],
        parameters={"source_account_id": "ACC-TREASURY-01", "destination_account_id": "ACC-VENDOR-2", "amount": "25000.00", "currency": "USD", "beneficiary_id": "BEN-2", "transaction_reference": f"REF-{uuid.uuid4().hex[:8].upper()}"},
        idempotency_key=f"idem-{uuid.uuid4()}",
    ))
    approval = db_session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == res.action_request_id))

    app.dependency_overrides[get_db] = override_get_db
    response = client.get(f"/api/v1/approvals/{approval.id}/approvers")
    assert response.status_code == 200
    body = response.json()
    approver_ids = [item["id"] for item in body["approvers"]]
    assert manifest["requester"]["id"] not in approver_ids
    assert manifest["approver"]["id"] in approver_ids
    assert str(other_bob.id) not in approver_ids
