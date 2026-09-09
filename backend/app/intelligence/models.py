"""Intelligence domain models.

Every intelligence output carries: source, evidence, confidence, reasoning,
timestamp, engine version, and provenance. No unexplained scores are ever returned.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


class IntelligenceSource(str, Enum):
    """Provenance of an intelligence signal."""
    RULE_ENGINE = "RULE_ENGINE"        # deterministic rule (always available)
    BASELINE = "BASELINE"              # behavioral baseline deviation
    CORPUS = "CORPUS"                  # derived from governance corpus patterns
    MODEL = "MODEL"                    # optional pluggable model provider (LLM etc.)
    AUDIT_HISTORY = "AUDIT_HISTORY"    # derived from prior audit events


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyLevel(str, Enum):
    NORMAL = "NORMAL"
    UNUSUAL = "UNUSUAL"
    SUSPICIOUS = "SUSPICIOUS"
    CRITICAL = "CRITICAL"


class ThreatType(str, Enum):
    """Normalized AgentOS threat taxonomy."""
    NONE = "none"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    PROMPT_INJECTION = "prompt_injection"
    TOOL_ABUSE = "tool_abuse"
    DATA_EXFILTRATION = "data_exfiltration"
    CROSS_TENANT_ACCESS = "cross_tenant_access"
    DELEGATION_ABUSE = "delegation_abuse"
    PAYLOAD_TAMPERING = "payload_tampering"
    REPLAY_ATTEMPT = "replay_attempt"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    POLICY_VIOLATION = "policy_violation"


class ThreatSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendationType(str, Enum):
    """What intelligence recommends. NEVER a final authorization."""
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    LIMIT_SCOPE = "LIMIT_SCOPE"
    REVOKE_DELEGATION = "REVOKE_DELEGATION"
    INVESTIGATE = "INVESTIGATE"


class IntentCategory(str, Enum):
    NORMAL = "NORMAL"                   # routine, well-scoped operation
    FINANCIAL = "FINANCIAL"             # money movement / payment
    DATA_ACCESS = "DATA_ACCESS"         # read/exfiltration-prone
    ADMINISTRATIVE = "ADMINISTRATIVE"   # config/privilege change
    COMMUNICATION = "COMMUNICATION"     # outbound messaging
    UNKNOWN = "UNKNOWN"


class CorpusProvenance(str, Enum):
    PUBLIC_SOURCE = "PUBLIC_SOURCE"
    SYNTHETIC = "SYNTHETIC"
    INTERNAL = "INTERNAL"


@dataclass(frozen=True)
class ActionContext:
    """Everything the intelligence layer may look at — built from server-side state only."""
    action_name: str
    action_risk_level: str                        # LOW/MEDIUM/HIGH (persisted enum)
    tool_name: str
    resource_type: str
    resource_key: str
    resource_sensitivity: str                     # LOW/MEDIUM/HIGH
    agent_name: str
    agent_risk_classification: str
    agent_id: str
    principal_id: str
    tenant_id: str
    delegation_scope: str
    parameters: dict[str, Any] = field(default_factory=dict)
    # Behavioral history (computed from audit/action history)
    prior_actions_count: int = 0
    prior_failures: int = 0
    prior_blocked: int = 0
    prior_tamper_attempts: int = 0
    prior_cross_tenant_attempts: int = 0
    prior_approval_rejections: int = 0
    # Context flags (server-derived, never client-supplied)
    is_first_action_for_agent: bool = False
    outside_normal_hours: bool = False
    context_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntelligenceEvidence:
    """A single piece of explainable evidence backing a signal."""
    source: IntelligenceSource
    fact: str                                      # human-readable fact
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    provenance: str = "agentos:deterministic"      # how this evidence was derived


@dataclass(frozen=True)
class RiskSignal:
    """Explainable risk contribution."""
    code: str
    label: str
    weight: int                                    # contribution to the score
    evidence: IntelligenceEvidence
    reasoning: str


@dataclass(frozen=True)
class RiskAssessment:
    """Complete risk assessment — never an unexplained number."""
    score: int                                     # 0-100
    level: RiskLevel
    factors: tuple[RiskSignal, ...]
    recommended_control: RecommendationType
    engine_version: str
    assessed_at: datetime
    confidence: float
    reasoning: str                                 # overall reasoning summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "level": self.level.value,
            "factors": [
                {"code": f.code, "label": f.label, "weight": f.weight,
                 "reasoning": f.reasoning, "evidence": {"source": f.evidence.source.value, "fact": f.evidence.fact}}
                for f in self.factors
            ],
            "recommended_control": self.recommended_control.value,
            "engine_version": self.engine_version,
            "assessed_at": self.assessed_at.isoformat(),
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


@dataclass(frozen=True)
class IntentAnalysis:
    """Result of intent analysis — pluggable provider abstraction."""
    normalized_intent: str
    category: IntentCategory
    confidence: float
    suspicious_indicators: tuple[str, ...]
    evidence: tuple[IntelligenceEvidence, ...]
    provider: str                                   # e.g. "rule_based_v1", "openai", "local"
    analyzed_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "normalized_intent": self.normalized_intent,
            "category": self.category.value,
            "confidence": self.confidence,
            "suspicious_indicators": list(self.suspicious_indicators),
            "evidence": [{"source": e.source.value, "fact": e.fact} for e in self.evidence],
            "provider": self.provider,
            "analyzed_at": self.analyzed_at.isoformat(),
        }


@dataclass(frozen=True)
class AnomalySignal:
    """Behavioral deviation from the baseline."""
    code: str
    label: str
    level: AnomalyLevel
    evidence: IntelligenceEvidence
    reasoning: str


@dataclass(frozen=True)
class AnomalyAssessment:
    """Complete anomaly assessment vs. behavioral baseline."""
    level: AnomalyLevel
    signals: tuple[AnomalySignal, ...]
    baseline_summary: dict[str, Any]                # what "normal" looks like
    engine_version: str
    assessed_at: datetime
    confidence: float
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.value,
            "signals": [
                {"code": s.code, "label": s.label, "level": s.level.value, "reasoning": s.reasoning}
                for s in self.signals
            ],
            "baseline_summary": self.baseline_summary,
            "engine_version": self.engine_version,
            "assessed_at": self.assessed_at.isoformat(),
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


@dataclass(frozen=True)
class ThreatSignal:
    """A classified threat detection."""
    threat_type: ThreatType
    severity: ThreatSeverity
    confidence: float
    evidence: IntelligenceEvidence
    reasoning: str
    recommended_action: RecommendationType


@dataclass(frozen=True)
class ThreatAssessment:
    """Complete threat classification."""
    threats: tuple[ThreatSignal, ...]
    highest_severity: ThreatSeverity
    engine_version: str
    assessed_at: datetime
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "threats": [
                {"type": t.threat_type.value, "severity": t.severity.value,
                 "confidence": t.confidence, "reasoning": t.reasoning,
                 "recommended_action": t.recommended_action.value,
                 "evidence": {"source": t.evidence.source.value, "fact": t.evidence.fact}}
                for t in self.threats
            ],
            "highest_severity": self.highest_severity.value,
            "engine_version": self.engine_version,
            "assessed_at": self.assessed_at.isoformat(),
            "reasoning": self.reasoning,
        }


@dataclass(frozen=True)
class PolicyRecommendation:
    """Intelligence recommendation — NEVER a final decision."""
    recommendation: RecommendationType
    confidence: float
    reasoning: str
    evidence: tuple[IntelligenceEvidence, ...]
    engine_version: str
    recommended_at: datetime
    # Explicitly disclaimed: this is advisory only
    is_advisory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation": self.recommendation.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "evidence": [{"source": e.source.value, "fact": e.fact} for e in self.evidence],
            "engine_version": self.engine_version,
            "recommended_at": self.recommended_at.isoformat(),
            "is_advisory": self.is_advisory,
            "disclaimer": "Intelligence recommends. The deterministic policy engine decides.",
        }


@dataclass(frozen=True)
class IntelligenceAssessment:
    """Complete intelligence assessment for a single action — the facade output."""
    assessment_id: str
    action_context_summary: dict[str, Any]
    risk: RiskAssessment
    intent: IntentAnalysis
    anomaly: AnomalyAssessment
    threats: ThreatAssessment
    policy_recommendation: PolicyRecommendation
    engine_version: str
    assessed_at: datetime
    overall_confidence: float
    reasoning: str
    # The FINAL decision always comes from the deterministic policy engine, never here
    deterministic_decision: str | None = None       # populated post-policy for audit trail

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "engine_version": self.engine_version,
            "assessed_at": self.assessed_at.isoformat(),
            "overall_confidence": self.overall_confidence,
            "reasoning": self.reasoning,
            "action_context_summary": self.action_context_summary,
            "risk": self.risk.to_dict(),
            "intent": self.intent.to_dict(),
            "anomaly": self.anomaly.to_dict(),
            "threats": self.threats.to_dict(),
            "policy_recommendation": self.policy_recommendation.to_dict(),
            "deterministic_decision": self.deterministic_decision,
            "security_rule": "AI/Intelligence recommends. The deterministic policy engine decides.",
        }
