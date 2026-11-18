"""Unit tests for HomeOps-AI v1.3.0 latency anomaly detection."""

import pytest

from homeops.anomaly_detection import detect_latency_anomaly


def test_normal_latency_is_not_anomaly():
    result = detect_latency_anomaly(23, [18, 20, 19, 22, 21, 20])
    assert result["is_anomaly"] is False
    assert result["baseline_samples"] == 6
    assert result["baseline_median_ms"] == 20


def test_large_latency_spike_is_anomaly():
    result = detect_latency_anomaly(250, [18, 20, 19, 22, 21, 20])
    assert result["is_anomaly"] is True
    assert result["type"] == "HIGH_LATENCY"
    assert "exceeds" in result["reason"]


def test_insufficient_history_does_not_trigger_anomaly():
    result = detect_latency_anomaly(500, [18, 20, 19, 22])
    assert result["is_anomaly"] is False
    assert result["threshold_ms"] is None
    assert "Insufficient history" in result["reason"]


@pytest.mark.parametrize("current", [None, -1, True, "slow"])
def test_invalid_current_latency_is_ignored(current):
    result = detect_latency_anomaly(current, [18, 20, 19, 22, 21])
    assert result["is_anomaly"] is False
    assert "No valid current" in result["reason"]


def test_invalid_historical_samples_are_ignored():
    result = detect_latency_anomaly(250, [18, None, -5, 20, True, 19, 22, 21])
    assert result["baseline_samples"] == 5
    assert result["is_anomaly"] is True


def test_threshold_is_strictly_exceeded():
    baseline = [20] * 5
    assert detect_latency_anomaly(70, baseline)["is_anomaly"] is False
    assert detect_latency_anomaly(70.01, baseline)["is_anomaly"] is True
