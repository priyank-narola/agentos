"""Intelligence API — exposes real intelligence assessments for the UI.

The /intelligence/assess endpoint runs the full intelligence pipeline on a
provisioned demo context and returns the explainable result. Advisory only.
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.intelligence.assessor import assess as run_intelligence
from app.intelligence.corpus import load_corpus, provenance_breakdown
from app.intelligence.evaluation import evaluate_intelligence
from app.db.models import Action, Agent, Principal, Resource, Tool
from sqlalchemy import select
import uuid as _uuid

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])


@router.get("/corpus/stats")
def corpus_stats() -> dict[str, Any]:
    """Corpus size and provenance breakdown."""
    data = load_corpus()
    return {
        "total": data["total"],
        "provenance": provenance_breakdown(data),
        "schema_version": data["schema_version"],
    }


@router.get("/evaluation")
def evaluation_results() -> dict[str, Any]:
    """Run the intelligence evaluation suite against the corpus."""
    return evaluate_intelligence()


@router.post("/assess-demo")
def assess_demo_context(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Run a full intelligence assessment on the treasury demo context (advisory).

    Uses the most recent governed action's real context if available; otherwise
    constructs a representative demo assessment. This is for UI demonstration
    of the intelligence layer — the deterministic policy engine remains authoritative.
    """
    # Find the most recent wire_transfer action request with its full context
    from app.db.models import ActionRequest
    req = db.scalar(
        select(ActionRequest)
        .where(ActionRequest.action.has(Action.name == "wire_transfer"))
        .order_by(ActionRequest.requested_at.desc())
        .limit(1)
    )
    if req is not None:
        agent = db.get(Agent, req.agent_id)
        principal = db.get(Principal, req.principal_id)
        action = db.get(Action, req.action_id)
        resource = db.get(Resource, req.resource_id)
        tool = db.get(Tool, action.tool_id) if action else None
        if all((agent, principal, action, tool, resource)):
            intel = run_intelligence(db, agent, principal, action, tool, resource, req.parameters or {}, req.tenant_id)
            return intel.to_dict()

    # Fallback: no governed wire actions yet — return empty state indicator
    return {
        "status": "NO_DATA",
        "message": "No governed wire_transfer actions exist yet. Run the Treasury Governance Demo first to populate real intelligence assessments.",
        "security_rule": "AI/Intelligence recommends. The deterministic policy engine decides.",
    }
