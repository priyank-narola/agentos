"""External Security Knowledge Ingestion Pipeline.

Imports security knowledge from authoritative sources (OWASP, NIST, CWE, MCP
security guidance) with full provenance. Items are structured as KnowledgeEntry
records — NOT raw scraped text. Provenance (source, URL, title, date, category,
original reference, ingestion timestamp) is mandatory and validated.

This module defines the ingestion contract; the actual knowledge entries are
curated JSON (data/ingested_knowledge.json) referencing public authoritative
sources — no blind scraping occurs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

KNOWLEDGE_PATH = Path(__file__).parent / "data" / "ingested_knowledge.json"

REQUIRED_KNOWLEDGE_FIELDS = [
    "id", "source", "source_url", "title", "category", "provenance",
    "original_reference", "ingested_at", "risk_factors", "threat_types",
]

VALID_SOURCES = {
    "OWASP_LLM_TOP10", "OWASP_AGENTIC", "NIST_AI_RMF", "NIST_CSF",
    "CWE", "MCP_SECURITY", "OAUTH_RFC", "ZERO_TRUST_NIST", "AI_INCIDENT",
}

VALID_CATEGORIES = {
    "prompt_injection", "tool_poisoning", "confused_deputy", "privilege_escalation",
    "delegation_abuse", "agent_impersonation", "data_exfiltration", "policy_manipulation",
    "cross_tenant_access", "replay", "malicious_tool", "unauthorized_financial",
    "supply_chain", "excessive_agency", "sensitive_data_disclosure", "insecure_output",
    "identity_spoofing", "audit_gaps", "human_oversight", "multi_agent_risk",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_knowledge() -> dict[str, Any]:
    """Load and validate the ingested knowledge base."""
    with open(KNOWLEDGE_PATH) as f:
        data = json.load(f)
    errors = []
    for i, entry in enumerate(data.get("entries", [])):
        for field in REQUIRED_KNOWLEDGE_FIELDS:
            if field not in entry or not entry[field]:
                errors.append(f"[{i}:{entry.get('id','?')}] missing '{field}'")
        if entry.get("source") not in VALID_SOURCES:
            errors.append(f"[{entry.get('id','?')}] invalid source '{entry.get('source')}'")
        if entry.get("category") not in VALID_CATEGORIES:
            errors.append(f"[{entry.get('id','?')}] invalid category '{entry.get('category')}'")
        if entry.get("provenance") != "PUBLIC_SOURCE":
            errors.append(f"[{entry.get('id','?')}] knowledge entries must be PUBLIC_SOURCE")
        if not entry.get("source_url", "").startswith("http"):
            errors.append(f"[{entry.get('id','?')}] source_url must be a valid http(s) URL")
    if errors:
        raise ValueError(f"Knowledge validation failed: {errors[:5]}... ({len(errors)} errors)")
    return data


def knowledge_by_category() -> dict[str, list[dict]]:
    """Group knowledge entries by category for intelligence enrichment."""
    data = load_knowledge()
    by_cat: dict[str, list[dict]] = {}
    for entry in data["entries"]:
        by_cat.setdefault(entry["category"], []).append(entry)
    return by_cat


def knowledge_by_threat_type(threat_type: str) -> list[dict]:
    """Find knowledge entries relevant to a specific threat type."""
    data = load_knowledge()
    return [e for e in data["entries"] if threat_type in e.get("threat_types", [])]
