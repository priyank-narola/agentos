"""Bounded in-process rate limiting for exposed AgentOS control-plane surfaces.

Design notes (proportional to a single-instance, localhost/sandbox deployment):
- In-memory fixed-window limiter per client IP. No distributed store is used;
  a multi-instance deployment would require a shared backend (e.g. Redis),
  which is intentionally out of scope until there is evidence it is needed.
- The limit is intentionally generous so normal API traffic and the test
  suite are unaffected; its purpose is abuse damping, not fine-grained quota.
- Enforcement is a FastAPI dependency so tests can override it per application.
"""

import threading
import time

from fastapi import Depends, HTTPException, Request, status

from app.config import settings


class FixedWindowRateLimiter:
    """Fixed-window per-key rate limiter (thread-safe, bounded memory)."""

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._windows: dict[str, tuple[int, int]] = {}  # key -> (window_start, count)

    def _reset_if_expired(self, key: str, now: int) -> tuple[int, int]:
        window_start, count = self._windows.get(key, (now, 0))
        if now - window_start >= self.window_seconds:
            window_start, count = now, 0
        return window_start, count

    def allow(self, key: str) -> bool:
        now = int(time.monotonic())
        with self._lock:
            window_start, count = self._reset_if_expired(key, now)
            if count >= self.max_requests:
                self._windows[key] = (window_start, count)
                return False
            self._windows[key] = (window_start, count + 1)
            # Opportunistically bound memory by dropping stale keys occasionally.
            if len(self._windows) > 100_000:
                cutoff = now - self.window_seconds
                self._windows = {k: v for k, v in self._windows.items() if v[0] >= cutoff}
            return True


_limiter = FixedWindowRateLimiter(
    max_requests=settings.rate_limit_max,
    window_seconds=settings.rate_limit_window_seconds,
)


def get_client_key(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


def check_rate_limit(request: Request) -> None:
    """FastAPI dependency: reject the request with 429 when over the limit."""
    if not _limiter.allow(get_client_key(request)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again shortly.",
        )
