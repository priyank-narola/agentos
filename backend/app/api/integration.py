from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.mcp_sandbox import ExternalMCPSandboxClient

router = APIRouter(prefix="/api/v1/integration", tags=["integration-health-and-demo"])


@router.get("/health", response_model=dict[str, Any])
def get_integration_health(
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Read-only integration health check endpoint.
    Exposes component readiness across transport, auth, discovery, authorization, approval, execution, and audit.
    Never exposes secrets, tokens, or credentials.
    """
    client_sandbox = ExternalMCPSandboxClient(db)
    return client_sandbox.get_integration_health()


@router.post("/demo/ciso-flow", response_model=dict[str, Any])
def run_ciso_demo_flow(
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Executes the deterministic 13-step TreasuryBot $25,000 USD wire transfer CISO demonstration flow."""
    client_sandbox = ExternalMCPSandboxClient(db)
    return client_sandbox.run_ciso_demonstration_flow()


@router.post("/demo/attack-flow/{attack_type}", response_model=dict[str, Any])
def run_attack_demo_flow(
    attack_type: str,
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Executes deterministic live attack simulation flows proving all attacks fail closed."""
    client_sandbox = ExternalMCPSandboxClient(db)
    result = client_sandbox.run_live_attack_demonstration(attack_type)
    if result.get("outcome") == "UNKNOWN_ATTACK_TYPE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["reason"]
        )
    return result
