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
        """Return True if this provider is *configured* (credentials present).

        Configuration is necessary but NOT sufficient for the provider to work:
        the endpoint may be unreachable, the key rejected, or the account
        suspended. Never present ``is_available()`` to a user as "connected" —
        call :meth:`verify` for a claim backed by a real round-trip.
        """
        ...

    @abstractmethod
    def analyze(self, ctx: ActionContext) -> dict[str, Any]:
        """Return advisory intelligence enrichment as a dict with
        'source', 'confidence', 'evidence', and 'reasoning' keys.
        Must never include a final authorization decision."""
        ...

    def verify(self, force: bool = False) -> dict[str, Any]:
        """Probe the provider with a real request and report what is true.

        Returns a dict with ``configured``, ``reachable``, ``status`` and a
        redacted ``error``. The default implementation reports configuration
        only and explicitly declines to claim reachability, so a provider that
        does not implement a probe can never be rendered as "connected".
        """
        configured = self.is_available()
        return {
            "name": self.name,
            "configured": configured,
            "reachable": None,  # unknown — this provider implements no probe
            "status": "CONFIGURED_UNVERIFIED" if configured else "NOT_CONFIGURED",
            "error": None,
        }


class ModelProviderRegistry:
    """Registry of available model providers. Empty by default — no LLM required."""

    def __init__(self) -> None:
        self._providers: dict[str, IntelligenceModelProvider] = {}

    def register(self, provider: IntelligenceModelProvider) -> None:
        self._providers[provider.name] = provider

    def available(self) -> list[IntelligenceModelProvider]:
        """Providers that are *configured*. See ``IntelligenceModelProvider.is_available``."""
        return [p for p in self._providers.values() if p.is_available()]

    def registered(self) -> list[IntelligenceModelProvider]:
        """Every registered provider, configured or not."""
        return list(self._providers.values())

    def verify_all(self, force: bool = False) -> list[dict[str, Any]]:
        """Probe every registered provider and return honest per-provider status."""
        return [p.verify(force=force) for p in self._providers.values()]

    def get(self, name: str) -> IntelligenceModelProvider | None:
        return self._providers.get(name)


# Global registry — remains empty unless a provider is explicitly registered
_registry = ModelProviderRegistry()


def get_registry() -> ModelProviderRegistry:
    return _registry
