"""Model Provider Abstraction — optional pluggable intelligence providers.

The intelligence layer works WITHOUT any LLM (deterministic rules + baselines).
Future providers (OpenAI, Anthropic, Gemini, local models) implement
IntelligenceModelProvider and are registered here. They may only produce
advisory signals — never authorization decisions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.intelligence.models import (
    ActionContext, IntelligenceEvidence, IntelligenceSource,
)


class IntelligenceModelProvider(ABC):
    """Abstract base for optional model-backed intelligence providers.

    Implementations may enrich intent analysis, anomaly detection, or threat
    classification. They MUST NOT produce authorization decisions.
    """

    name: str = "abstract"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider is configured and reachable."""
        ...

    @abstractmethod
    def analyze(self, ctx: ActionContext) -> dict[str, Any]:
        """Return advisory intelligence enrichment as a dict with
        'source', 'confidence', 'evidence', and 'reasoning' keys.
        Must never include a final authorization decision."""
        ...


class ModelProviderRegistry:
    """Registry of available model providers. Empty by default — no LLM required."""

    def __init__(self) -> None:
        self._providers: dict[str, IntelligenceModelProvider] = {}

    def register(self, provider: IntelligenceModelProvider) -> None:
        self._providers[provider.name] = provider

    def available(self) -> list[IntelligenceModelProvider]:
        return [p for p in self._providers.values() if p.is_available()]

    def get(self, name: str) -> IntelligenceModelProvider | None:
        return self._providers.get(name)


# Global registry — remains empty unless a provider is explicitly registered
_registry = ModelProviderRegistry()


def get_registry() -> ModelProviderRegistry:
    return _registry
