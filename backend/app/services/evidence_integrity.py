"""Canonical integrity digests for portable evidence exports."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.schemas import ActionEvidenceBundle, EvidenceIntegrity


def canonical_evidence_payload(bundle: ActionEvidenceBundle) -> dict[str, Any]:
    """Return the stable fields covered by an export integrity digest.

    ``exported_at`` is intentionally excluded: the same unchanged action must
    produce the same evidence digest whenever it is exported. The digest is an
    integrity check for the portable record, not a digital signature or proof
    of an external provider outcome.
    """
    return bundle.model_dump(mode="json", exclude={"exported_at", "integrity"})


def build_evidence_integrity(bundle: ActionEvidenceBundle) -> EvidenceIntegrity:
    encoded = json.dumps(canonical_evidence_payload(bundle), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return EvidenceIntegrity(algorithm="SHA-256", digest=hashlib.sha256(encoded).hexdigest())


def verify_evidence_integrity(bundle: ActionEvidenceBundle) -> bool:
    """Verify an already-exported record without querying or mutating storage."""
    return bundle.integrity.digest == build_evidence_integrity(bundle).digest
