"""Lightweight statistical anomaly detection for HomeOps-AI v1.3.0.

This module does not modify the database or send alerts. It detects unusually
high latency from historical measurements using a robust median/MAD baseline.
"""

from statistics import median
from typing import Iterable, Optional


MIN_BASELINE_SAMPLES = 5
MIN_ABSOLUTE_INCREASE_MS = 50.0
MAD_MULTIPLIER = 3.0


def detect_latency_anomaly(
    current_latency_ms: Optional[float],
    historical_latencies_ms: Iterable[Optional[float]],
) -> dict:
    """Evaluate a latency measurement against prior valid observations.

    Historical values must exclude the current measurement. Missing or negative
    measurements are ignored. Returns a structured result with an explanation.
    """
    baseline = [
        float(value)
        for value in historical_latencies_ms
        if value is not None and isinstance(value, (int, float))
        and not isinstance(value, bool) and value >= 0
    ]
    result = {
        "is_anomaly": False,
        "type": "HIGH_LATENCY",
        "current_latency_ms": current_latency_ms,
        "baseline_samples": len(baseline),
        "baseline_median_ms": None,
        "threshold_ms": None,
        "reason": "",
    }

    if current_latency_ms is None or not isinstance(current_latency_ms, (int, float)) or isinstance(current_latency_ms, bool) or current_latency_ms < 0:
        result["reason"] = "No valid current latency measurement."
        return result

    if len(baseline) < MIN_BASELINE_SAMPLES:
        result["reason"] = (
            f"Insufficient history: {len(baseline)} valid samples; "
            f"at least {MIN_BASELINE_SAMPLES} required."
        )
        return result

    typical = median(baseline)
    deviations = [abs(value - typical) for value in baseline]
    mad = median(deviations)
    # 1.4826 scales MAD to a standard-deviation estimate for normal data.
    robust_spread = 1.4826 * mad
    threshold = typical + max(MIN_ABSOLUTE_INCREASE_MS, MAD_MULTIPLIER * robust_spread)

    result["baseline_median_ms"] = round(typical, 2)
    result["threshold_ms"] = round(threshold, 2)
    result["is_anomaly"] = current_latency_ms > threshold
    if result["is_anomaly"]:
        result["reason"] = (
            f"Latency {current_latency_ms:.1f} ms exceeds the historical "
            f"threshold of {threshold:.1f} ms (median {typical:.1f} ms)."
        )
    else:
        result["reason"] = "Latency is within the historical threshold."
    return result
