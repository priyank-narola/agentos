"""Tests for payload-free operational runtime metrics."""

from app.runtime import RuntimeMetrics


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
