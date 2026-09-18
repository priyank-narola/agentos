"""Tests for payload-free operational runtime metrics and logs."""

import json
import logging
import sys

from app.runtime import JsonLogFormatter, RuntimeMetrics


def test_runtime_metrics_aggregate_status_and_latency_without_request_labels() -> None:
    metrics = RuntimeMetrics()
    metrics.record(status_code=200, duration_ms=12.345)
    metrics.record(status_code=503, duration_ms=7.2)

    snapshot = metrics.snapshot()

    assert snapshot["request_total"] == 2
    assert snapshot["failed_request_total"] == 1
    assert snapshot["average_latency_ms"] == 9.77
    assert snapshot["max_latency_ms"] == 12.35
    assert snapshot["status_counts"] == {"200": 1, "503": 1}
    assert snapshot["scope"] == "single_process_payload_free"
    assert "path" not in snapshot
    assert "tenant" not in snapshot


def test_runtime_metrics_counts_unhandled_failure_even_if_status_is_not_server_error() -> None:
    metrics = RuntimeMetrics()
    metrics.record(status_code=499, duration_ms=3, failed=True)

    assert metrics.snapshot()["failed_request_total"] == 1


def test_json_log_formatter_allows_only_safe_operational_extra_fields() -> None:
    logger = logging.getLogger("agentos.test")
    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        __file__,
        1,
        "action completed",
        (),
        None,
        extra={
            "event": "http_request_completed",
            "request_id": "req-12345678",
            "method": "POST",
            "path": "/api/v1/actions",
            "status_code": 201,
            "duration_ms": 12.5,
            "authorization": "Bearer secret-token",
            "parameters": {"customer_email": "person@example.test", "amount": 25000},
            "provider_payload": {"secret": "do-not-log"},
        },
    )

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["event"] == "http_request_completed"
    assert payload["request_id"] == "req-12345678"
    assert payload["path"] == "/api/v1/actions"
    assert payload["status_code"] == 201
    assert "authorization" not in payload
    assert "parameters" not in payload
    assert "provider_payload" not in payload
    assert "person@example.test" not in json.dumps(payload)


def test_json_log_formatter_does_not_emit_exception_message_or_stack() -> None:
    logger = logging.getLogger("agentos.test")
    try:
        raise ValueError("provider response included person@example.test and secret data")
    except ValueError:
        record = logger.makeRecord(
            logger.name,
            logging.ERROR,
            __file__,
            1,
            "provider request failed",
            (),
            exc_info=sys.exc_info(),
            extra={"event": "provider_request_failed", "provider_payload": {"secret": "do-not-log"}},
        )

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["exception_type"] == "ValueError"
    assert "exception" not in payload
    assert "person@example.test" not in json.dumps(payload)
    assert "provider_payload" not in payload
