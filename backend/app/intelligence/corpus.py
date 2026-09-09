"""Corpus loader — loads and validates the governance corpus JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CORPUS_PATH = Path(__file__).parent / "data" / "governance_corpus.json"

REQUIRED_FIELDS = [
    "id", "provenance", "source", "threat_type", "expected_decision",
    "explanation", "severity", "risk_factors", "approval_requirement",
]

VALID_PROVENANCE = {"PUBLIC_SOURCE", "SYNTHETIC", "INTERNAL"}
VALID_DECISIONS = {"ALLOW", "DENY", "REQUIRE_APPROVAL"}


def load_corpus() -> dict[str, Any]:
    """Load the corpus and validate every entry has required fields with provenance."""
    with open(CORPUS_PATH) as f:
        data = json.load(f)
    errors = []
    for i, s in enumerate(data.get("scenarios", [])):
        for field in REQUIRED_FIELDS:
            if field not in s:
                errors.append(f"[{i}] missing field '{field}'")
        if s.get("provenance") not in VALID_PROVENANCE:
            errors.append(f"[{i}] invalid provenance '{s.get('provenance')}'")
        if s.get("expected_decision") not in VALID_DECISIONS:
            errors.append(f"[{i}] invalid expected_decision '{s.get('expected_decision')}'")
        if not s.get("source"):
            errors.append(f"[{i}] missing source/provenance note")
    if errors:
        raise ValueError(f"Corpus validation failed: {errors[:5]}... ({len(errors)} total errors)")
    return data


def provenance_breakdown(data: dict[str, Any]) -> dict[str, int]:
    prov: dict[str, int] = {}
    for s in data["scenarios"]:
        prov[s["provenance"]] = prov.get(s["provenance"], 0) + 1
    return prov
