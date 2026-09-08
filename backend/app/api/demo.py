from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.services.demo import FinancialWorkflowDemoService

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


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
