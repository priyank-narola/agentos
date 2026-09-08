"""PostgreSQL-backed end-to-end coverage of critical system boundaries (W7).

Gated behind AGENTOS_TEST_POSTGRES_URL and destructive on that database (schema is
recreated). Exercises: treasury bootstrap -> gateway -> risk/policy -> SoD approval
-> TOCTOU -> sandbox execution -> FinancialExecution ledger -> audit -> observability,
plus tenant posture, on real PostgreSQL with native enums and FKs.

Run:
    AGENTOS_TEST_POSTGRES_URL="postgresql+psycopg://postgres:postgres@localhost:5432/<scratch>" \
        python -m pytest tests/test_e2e_postgres.py
"""

import os
import uuid

import pytest
import sqlalchemy as sa

from app.db.base import Base
from app.db import models  # noqa: F401
from app.services.demo import treasury_demo_manifest
from app.services.gateway import GatewayService
from app.services.approval import ApprovalService
from app.services.observability import ObservabilityService
from app.schemas import GatewayRequestCreate, ApprovalActionRequest
from app.db.models import ApprovalRequest, FinancialExecution, ExecutionState, AuditEvent

URL = os.getenv("AGENTOS_TEST_POSTGRES_URL")

pytestmark = pytest.mark.skipif(
    not URL,
    reason="AGENTOS_TEST_POSTGRES_URL not set; PG E2E requires a real PostgreSQL database.",
)


@pytest.fixture(scope="module")
def engine():
    e = sa.create_engine(URL)
    with e.begin() as conn:
        conn.execute(sa.text("DROP SCHEMA public CASCADE"))
        conn.execute(sa.text("CREATE SCHEMA public"))
    Base.metadata.create_all(e)
    yield e
    with e.begin() as conn:
        conn.execute(sa.text("DROP SCHEMA public CASCADE"))
        conn.execute(sa.text("CREATE SCHEMA public"))
    e.dispose()


def test_full_governance_flow_on_postgres(engine):
    from sqlalchemy.orm import Session
    with Session(engine) as db:
        manifest = treasury_demo_manifest(db)
        params = {
            "source_account_id": manifest["resource"]["resource_key"],
            "destination_account_id": "ACC-VENDOR-E2E",
            "amount": "25000.00",
            "currency": "USD",
            "beneficiary_id": "BEN-E2E",
            "transaction_reference": f"REF-{uuid.uuid4().hex[:8].upper()}",
        }
        gw = GatewayService(db).submit(GatewayRequestCreate(
            principal_id=manifest["requester"]["id"], agent_id=manifest["agent"]["id"],
            action_id=manifest["action"]["id"], resource_id=manifest["resource"]["id"],
            parameters=params, idempotency_key=f"e2e-{uuid.uuid4()}",
        ))
        assert gw.gateway_status == "PENDING_APPROVAL"
        assert gw.risk_score == 75

        approval = db.query(ApprovalRequest).filter_by(action_request_id=gw.action_request_id).one()
        # SoD: requester cannot approve; the failed self-approval rejects that approval.
        import pytest as _pt
        from app.services.approval import ApprovalConflictError
        with _pt.raises(ApprovalConflictError):
            ApprovalService(db).approve(approval.id, ApprovalActionRequest(approver_principal_id=manifest["requester"]["id"]))

        # A second request approved by the independent approver completes end-to-end
        # (TOCTOU revalidation runs against PG rows).
        gw2 = GatewayService(db).submit(GatewayRequestCreate(
            principal_id=manifest["requester"]["id"], agent_id=manifest["agent"]["id"],
            action_id=manifest["action"]["id"], resource_id=manifest["resource"]["id"],
            parameters=params, idempotency_key=f"e2e-{uuid.uuid4()}",
        ))
        approval2 = db.query(ApprovalRequest).filter_by(action_request_id=gw2.action_request_id).one()
        detail = ApprovalService(db).approve(approval2.id, ApprovalActionRequest(approver_principal_id=manifest["approver"]["id"]))
        assert detail.status.value == "APPROVED"

        ledger = db.query(FinancialExecution).filter_by(action_request_id=gw2.action_request_id).one()
        assert ledger.status == ExecutionState.SUCCEEDED
        assert str(ledger.tenant_id) == manifest["tenant_id"]

        audit_count = db.query(AuditEvent).filter_by(action_request_id=gw2.action_request_id).count()
        assert audit_count >= 6

        obs = ObservabilityService(db)
        metrics = obs.get_security_dashboard_metrics(tenant_id=uuid.UUID(manifest["tenant_id"]))
        assert metrics["approved_executions"] >= 1
        posture = obs.get_tenant_security_posture(tenant_id=uuid.UUID(manifest["tenant_id"]))
        assert posture["execution_volume"] >= 1
        assert posture["high_risk_activity"] >= 1
