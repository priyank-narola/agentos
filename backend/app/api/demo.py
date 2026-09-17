from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.services.demo import FinancialWorkflowDemoService, customer_remediation_demo_manifest, treasury_demo_manifest
from app.api.ratelimit import check_rate_limit

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


@router.post("/treasury/bootstrap", dependencies=[Depends(check_rate_limit)])
def bootstrap_treasury_demo(
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Provision (or idempotently reuse) the flagship treasury demo environment:
    Global Treasury Corp tenant with Alice Smith (requester), Bob Jones
    (approver), TreasuryBot-v1 agent, wire_transfer action, and the sandbox
    treasury account. Returns a manifest of identities and targets for the UI.
    Idempotent: repeated calls reuse the existing environment and never create
    duplicate tenants, tools, principals, or actions.
    """
    return treasury_demo_manifest(db)


@router.post("/customer-remediation/bootstrap", dependencies=[Depends(check_rate_limit)])
def bootstrap_customer_remediation_demo(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Provision the sandbox customer-refund pilot workflow and return its manifest."""
    return customer_remediation_demo_manifest(db)


@router.post("/financial-workflow")
def execute_financial_workflow_demo(
    amount: str = "25000.00",
    currency: str = "USD",
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Executes the AgentOS Phase 3D End-to-End Enterprise Financial Agent Workflow Sandbox Demo.
    Demonstrates: AI Agent -> MCP Auth -> Multi-Tenant -> Identity -> Gateway -> Risk -> Policy -> Separation of Duties -> TOCTOU Revalidation -> Sandbox Provider -> Audit Trail.
    Zero real money movement. Safe sandbox execution.
    """
    service = FinancialWorkflowDemoService(db)
    return service.run_e2e_demo(amount=amount, currency=currency)
