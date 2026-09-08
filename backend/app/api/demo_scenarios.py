from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.scenarios import ScenarioEngine
from app.api.ratelimit import check_rate_limit

router = APIRouter(prefix="/api/v1/demo", tags=["demo-scenarios"])


@router.get("/scenarios", response_model=dict[str, Any])
def list_demo_scenarios() -> dict[str, Any]:
    """Lists the 8 deterministic enterprise financial agent demonstration scenarios (A-H)."""
    return {
        "total_scenarios": 8,
        "scenarios": [
            {"key": "SCENARIO_A", "name": "Scenario A: Low-Risk Transaction (Auto-Allowed)", "description": "Small approved payment, policy allows, no approval required, sandbox succeeds."},
            {"key": "SCENARIO_B", "name": "Scenario B: High-Risk Transaction (Approved)", "description": "High-value wire, risk HIGH/CRITICAL, approval required, independent approver approves, TOCTOU passes, sandbox succeeds."},
            {"key": "SCENARIO_C", "name": "Scenario C: Unauthorized Transaction (Denied)", "description": "Unauthorized transaction, policy denies, execution never occurs."},
            {"key": "SCENARIO_D", "name": "Scenario D: Payload Tampering Attack", "description": "Transaction modified after approval, payload digest mismatch detected, execution blocked."},
            {"key": "SCENARIO_E", "name": "Scenario E: Revoked Agent Delegation (TOCTOU)", "description": "Pending approval, agent/delegation revoked, approval attempt fails during TOCTOU revalidation."},
            {"key": "SCENARIO_F", "name": "Scenario F: Cross-Tenant Isolation Defense", "description": "Agent attempts to access another tenant's resource, fails closed, no cross-tenant data exposed."},
            {"key": "SCENARIO_G", "name": "Scenario G: Provider Failure & Timeout Handling", "description": "Approved transaction reaches sandbox provider, provider returns failure/timeout, execution state transitions correctly."},
            {"key": "SCENARIO_H", "name": "Scenario H: Duplicate Execution Prevention", "description": "Same idempotency key submitted twice, first request executes, second request cannot cause duplicate execution."}
        ]
    }


@router.post("/scenarios/{scenario_key}/run", response_model=dict[str, Any], dependencies=[Depends(check_rate_limit)])
def run_demo_scenario(
    scenario_key: str,
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Executes a deterministic enterprise demonstration scenario (A-H).
    NEVER accepts caller-supplied identity, tenant, risk, approval, or execution state.
    """
    engine = ScenarioEngine(db)
    key = scenario_key.upper()

    if key in ["SCENARIO_A", "A"]:
        return engine.run_scenario_a_low_risk()
    elif key in ["SCENARIO_B", "B"]:
        return engine.run_scenario_b_high_risk()
    elif key in ["SCENARIO_C", "C"]:
        return engine.run_scenario_c_rejected()
    elif key in ["SCENARIO_D", "D"]:
        return engine.run_scenario_d_tampered()
    elif key in ["SCENARIO_E", "E"]:
        return engine.run_scenario_e_revoked_agent()
    elif key in ["SCENARIO_F", "F"]:
        return engine.run_scenario_f_cross_tenant()
    elif key in ["SCENARIO_G", "G"]:
        return engine.run_scenario_g_provider_failure()
    elif key in ["SCENARIO_H", "H"]:
        return engine.run_scenario_h_duplicate()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario_key '{scenario_key}'. Expected one of: SCENARIO_A through SCENARIO_H."
        )


@router.get("/summary", response_model=dict[str, Any])
def get_control_plane_summary(
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Returns deterministic control plane summary metrics across all sandbox scenarios."""
    engine = ScenarioEngine(db)
    return engine.get_control_plane_summary()


@router.get("/audit-chain/{request_id}", response_model=dict[str, Any])
def get_audit_chain_trace(
    request_id: UUID,
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Exposes complete 12-step audit chain trace:
    REQUEST -> AUTHENTICATE -> IDENTIFY -> DELEGATE -> AUTHORIZE -> RISK -> POLICY -> APPROVAL -> REVALIDATE -> EXECUTE -> VERIFY -> AUDIT.
    """
    engine = ScenarioEngine(db)
    trace = engine.get_audit_chain_trace(request_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ActionRequest {request_id} not found"
        )
    return trace
