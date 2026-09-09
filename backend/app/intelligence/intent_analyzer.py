"""Intent Analysis — provider abstraction.

The IntentAnalyzer ABC allows future pluggable model providers (OpenAI, Anthropic,
Gemini, local models) without hard-wiring any LLM. The default RuleBasedIntentProvider
is deterministic and always available.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from app.intelligence.models import (
    ActionContext, IntentAnalysis, IntentCategory, IntelligenceEvidence,
    IntelligenceSource,
)

PROVIDER_NAME = "rule_based_v1"

# Action-name → intent category mapping
_CATEGORY_RULES: list[tuple[str, IntentCategory]] = [
    ("transfer", IntentCategory.FINANCIAL),
    ("payment", IntentCategory.FINANCIAL),
    ("payout", IntentCategory.FINANCIAL),
    ("refund", IntentCategory.FINANCIAL),
    ("invoice", IntentCategory.FINANCIAL),
    ("wire", IntentCategory.FINANCIAL),
    ("read", IntentCategory.DATA_ACCESS),
    ("fetch", IntentCategory.DATA_ACCESS),
    ("query", IntentCategory.DATA_ACCESS),
    ("export", IntentCategory.DATA_ACCESS),
    ("download", IntentCategory.DATA_ACCESS),
    ("update", IntentCategory.ADMINISTRATIVE),
    ("create", IntentCategory.ADMINISTRATIVE),
    ("delete", IntentCategory.ADMINISTRATIVE),
    ("modify", IntentCategory.ADMINISTRATIVE),
    ("configure", IntentCategory.ADMINISTRATIVE),
    ("grant", IntentCategory.ADMINISTRATIVE),
    ("revoke", IntentCategory.ADMINISTRATIVE),
    ("suspend", IntentCategory.ADMINISTRATIVE),
    ("send", IntentCategory.COMMUNICATION),
    ("email", IntentCategory.COMMUNICATION),
    ("notify", IntentCategory.COMMUNICATION),
    ("post", IntentCategory.COMMUNICATION),
]

_SUSPICIOUS_PARAM_MARKERS = [
    "ignore previous", "system prompt", "you are now", "disregard",
    "override", "jailbreak", "exfiltrate", "bypass", "admin_key",
]


class IntentAnalyzer(ABC):
    """Abstract intent analysis provider."""

    @abstractmethod
    def analyze(self, ctx: ActionContext) -> IntentAnalysis:
        """Analyze the intent of an action from its context."""
        ...


class RuleBasedIntentProvider(IntentAnalyzer):
    """Deterministic rule-based intent analysis — always available, no LLM required."""

    def analyze(self, ctx: ActionContext) -> IntentAnalysis:
        action_lower = ctx.action_name.lower()
        evidence: list[IntelligenceEvidence] = []
        suspicious: list[str] = []

        # Classify by action name
        category = IntentCategory.UNKNOWN
        for prefix, cat in _CATEGORY_RULES:
            if prefix in action_lower:
                category = cat
                break
        if category == IntentCategory.UNKNOWN:
            category = IntentCategory.ADMINISTRATIVE  # safe default for unrecognized

        evidence.append(IntelligenceEvidence(
            source=IntelligenceSource.RULE_ENGINE,
            fact=f"Action name '{ctx.action_name}' maps to intent category {category.value}.",
        ))

        # Financial intent specifics
        if category == IntentCategory.FINANCIAL:
            amount = ctx.parameters.get("amount")
            if amount is not None:
                evidence.append(IntelligenceEvidence(
                    source=IntelligenceSource.RULE_ENGINE,
                    fact=f"Financial parameters present: amount={amount}, currency={ctx.parameters.get('currency', 'N/A')}.",
                ))
                normalized = f"Execute a financial {ctx.action_name} of {amount} {ctx.parameters.get('currency', '')}".strip()
            else:
                normalized = f"Execute a financial {ctx.action_name} without explicit amount"
        elif category == IntentCategory.DATA_ACCESS:
            normalized = f"Access data via {ctx.action_name} on {ctx.resource_type}/{ctx.resource_key}"
        elif category == IntentCategory.ADMINISTRATIVE:
            normalized = f"Perform administrative {ctx.action_name} on {ctx.resource_type}/{ctx.resource_key}"
        elif category == IntentCategory.COMMUNICATION:
            normalized = f"Send communication via {ctx.action_name}"
        else:
            normalized = f"Perform {ctx.action_name} on {ctx.resource_type}/{ctx.resource_key}"

        # Suspicious indicators from parameters
        param_text = " ".join(str(v) for v in ctx.parameters.values()).lower()
        for marker in _SUSPICIOUS_PARAM_MARKERS:
            if marker in param_text:
                suspicious.append(f"Parameter contains '{marker}'")
        if suspicious:
            evidence.append(IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact=f"Suspicious indicators detected: {suspicious}.",
            ))

        # Suspicious: delegation scope mismatch
        action_verb = ctx.action_name.split("_")[0] if "_" in ctx.action_name else ctx.action_name
        if ctx.delegation_scope not in ("*", "none") and not (
            ctx.delegation_scope == ctx.action_name
            or ctx.delegation_scope.endswith(f".{action_verb}")
        ):
            suspicious.append(f"Action '{ctx.action_name}' may exceed delegated scope '{ctx.delegation_scope}'")

        confidence = 0.75 if category != IntentCategory.UNKNOWN else 0.4
        if suspicious:
            confidence = min(confidence + 0.1, 0.95)

        return IntentAnalysis(
            normalized_intent=normalized,
            category=category,
            confidence=confidence,
            suspicious_indicators=tuple(suspicious),
            evidence=tuple(evidence),
            provider=PROVIDER_NAME,
            analyzed_at=datetime.now(timezone.utc),
        )
