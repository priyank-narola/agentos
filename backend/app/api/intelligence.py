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
from app.intelligence.knowledge_base import load_knowledge
from app.intelligence.benchmark import run_model_vs_rule_benchmark, save_benchmark, load_benchmarks
from app.intelligence.providers import get_registry
from app.intelligence.openai_provider import register_if_configured
from app.db.models import Action, Agent, Principal, Resource, Tool
from sqlalchemy import select
import uuid as _uuid

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])

# Register model providers if configured
register_if_configured(get_registry())


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


@router.get("/knowledge/stats")
def knowledge_stats() -> dict[str, Any]:
    """Knowledge base size and source breakdown."""
    data = load_knowledge()
    sources = {}
    categories = {}
    for e in data["entries"]:
        sources[e["source"]] = sources.get(e["source"], 0) + 1
        categories[e["category"]] = categories.get(e["category"], 0) + 1
    return {"total": data["total"], "sources": sources, "categories": categories, "version": data["version"]}


@router.get("/models")
def model_status(verify: bool = True, force: bool = False) -> dict[str, Any]:
    """Report the *verified* state of intelligence model providers.

    Configuration alone is never reported as "connected": each configured
    provider is probed with a real round-trip so an upstream 401, WAF block, or
    outage is surfaced honestly rather than rendered as a healthy model. No
    credential is ever included in the response.
    """
    registry = get_registry()

    providers = registry.verify_all(force=force) if verify else [
        {"name": p.name, "configured": p.is_available(), "reachable": None,
         "status": "CONFIGURED_UNVERIFIED" if p.is_available() else "NOT_CONFIGURED", "error": None}
        for p in registry.registered()
    ]

    active = [p for p in providers if p.get("status") == "ACTIVE"]
    configured = [p for p in providers if p.get("configured")]

    if active:
        overall = "MODEL_ACTIVE"
        summary = f"{', '.join(p['name'] for p in active)} verified reachable"
    elif configured:
        overall = "MODEL_CONFIGURED_UNAVAILABLE"
        summary = "A model provider is configured but did not respond successfully. Running on deterministic intelligence."
    else:
        overall = "RULES_ONLY"
        summary = "No model provider configured. Running on deterministic intelligence."

    return {
        # Back-compatible shape: `available` stays "verified usable".
        "available": [{"name": p["name"], "available": True} for p in active],
        "configured": [
            {"name": p["name"], "configured": True, "ready": p.get("status") == "ACTIVE"}
            for p in configured
        ],
        "providers": providers,
        "status": overall,
        "summary": summary,
        "governance_rule": "Model intelligence is advisory only. The deterministic policy engine decides.",
        "note": "Intelligence works fully without any model. Models are optional advisory providers.",
    }


@router.get("/benchmark")
def run_benchmark() -> dict[str, Any]:
    """Run the model-vs-rule benchmark and persist results."""
    benchmark = run_model_vs_rule_benchmark(sample_size=50)
    save_benchmark(benchmark)
    return benchmark


@router.get("/benchmarks")
def list_benchmarks() -> dict[str, Any]:
    """List previously stored benchmark results."""
    benchmarks = load_benchmarks()
    return {"count": len(benchmarks), "benchmarks": benchmarks}


def _env_values() -> dict[str, Any]:
    import os
    return {
        "AGENTOS_MODEL_PROVIDER": os.getenv("AGENTOS_MODEL_PROVIDER", ""),
        "AGENTOS_MODEL_BASE_URL": os.getenv("AGENTOS_MODEL_BASE_URL", ""),
        "AGENTOS_MODEL_API_KEY": "set" if os.getenv("AGENTOS_MODEL_API_KEY") else "",
        "AGENTOS_MODEL_NAME": os.getenv("AGENTOS_MODEL_NAME", ""),
    }


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
