"""Small, dependency-free runtime operations helpers.

The application deliberately emits structured operational events without
recording request bodies, tokens, action parameters, or other customer data.
It is a baseline for a production log pipeline, not a replacement for a
centralized log/trace/alerting service.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from threading import Lock
from time import perf_counter
from uuid import uuid4

from fastapi import Request

from app.config import Settings

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,128}$")
# Structured operational logs must remain useful without becoming an accidental
# customer-data store. New call sites may opt into these fields only; arbitrary
# ``extra`` values (for example tokens, action parameters, email addresses, or
# provider payloads) are intentionally ignored.
_SAFE_LOG_EXTRA_FIELDS = frozenset({"event", "request_id", "method", "path", "status_code", "duration_ms"})


class RuntimeMetrics:
    """Process-local, payload-free runtime telemetry.

    This is deliberately small and has no path, tenant, request-id, user, or
    payload labels. It gives an operator immediate release/sandbox visibility
    without creating a customer-data telemetry store. Multi-instance alerting
    and retention belong in the selected production observability platform.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._started_at = datetime.now(timezone.utc)
        self._request_total = 0
        self._failed_total = 0
        self._latency_total_ms = 0.0
        self._latency_max_ms = 0.0
        self._status_counts: Counter[str] = Counter()

    def record(self, *, status_code: int, duration_ms: float, failed: bool = False) -> None:
        with self._lock:
            self._request_total += 1
            self._failed_total += int(failed or status_code >= 500)
            self._latency_total_ms += duration_ms
            self._latency_max_ms = max(self._latency_max_ms, duration_ms)
            self._status_counts[str(status_code)] += 1

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            now = datetime.now(timezone.utc)
            return {
                "started_at": self._started_at.isoformat(),
                "uptime_seconds": round((now - self._started_at).total_seconds(), 2),
                "request_total": self._request_total,
                "failed_request_total": self._failed_total,
                "average_latency_ms": round(self._latency_total_ms / self._request_total, 2) if self._request_total else 0.0,
                "max_latency_ms": round(self._latency_max_ms, 2),
                "status_counts": dict(sorted(self._status_counts.items())),
                "scope": "single_process_payload_free",
            }


runtime_metrics = RuntimeMetrics()


class JsonLogFormatter(logging.Formatter):
    """Render a safe, compact JSON object for standard output collectors."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in _SAFE_LOG_EXTRA_FIELDS:
            value = record.__dict__.get(key)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_logging(current: Settings) -> None:
    """Configure a single stdout handler exactly once per application process."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, current.log_level, logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    if current.log_format == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.handlers = [handler]


def request_id_from(request: Request) -> str:
    """Accept only a safe correlation identifier, otherwise generate one."""
    candidate = request.headers.get("X-Request-ID", "")
    return candidate if _REQUEST_ID_PATTERN.fullmatch(candidate) else str(uuid4())


async def log_request(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Attach a correlation ID and emit one completion record per HTTP request."""
    request_id = request_id_from(request)
    started_at = perf_counter()
    logger = logging.getLogger("agentos.http")
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        runtime_metrics.record(status_code=500, duration_ms=duration_ms, failed=True)
        logger.exception(
            "http_request_failed",
            extra={
                "event": "http_request_failed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )
        raise
    response.headers["X-Request-ID"] = request_id
    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    runtime_metrics.record(status_code=response.status_code, duration_ms=duration_ms)
    logger.info(
        "http_request_completed",
        extra={
            "event": "http_request_completed",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response
