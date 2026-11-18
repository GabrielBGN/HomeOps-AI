"""Tests for HomeOps-AI OpenAI integration."""

import json
from unittest.mock import MagicMock

import pytest

from homeops.ai_analyst import (
    NetworkAnalysisError,
    analyze_network_health,
)


@pytest.fixture
def sanitized_summary():
    """Generate valid, anonymized network data for integration tests."""
    from homeops.ai_analyst import build_network_health_summary

    devices = [
        (
            "192.168.1.10",
            "AA:BB:CC:DD:EE:01",
            "Test-PC",
            "Test Vendor",
            "2026-11-01",
            "2026-11-18",
            "ONLINE",
            0,
        ),
        (
            "192.168.1.20",
            "AA:BB:CC:DD:EE:02",
            "Test-TV",
            "Test Vendor",
            "2026-11-01",
            "2026-11-18",
            "OFFLINE",
            1,
        ),
    ]

    return build_network_health_summary(
        devices=devices,
        availability=[],
        alerts=[],
        scan_history=[],
        latency_histories={},
    )


@pytest.fixture
def sample_report():
    return {
        "overall_health": "DEGRADED",
        "severity": "MEDIUM",
        "executive_summary": "One device is offline.",
        "findings": ["One of two devices is offline."],
        "recommendations": ["Check the device connection."],
        "limitations": ["Insufficient historical data."],
    }


def test_successful_ai_analysis(sanitized_summary, sample_report):
    client = MagicMock()
    client.responses.create.return_value.status = "completed"
    client.responses.create.return_value.output_text = json.dumps(
        sample_report
    )

    result = analyze_network_health(
        sanitized_summary,
        client=client,
        model="test-model",
    )

    assert result == sample_report
    client.responses.create.assert_called_once()

    request = client.responses.create.call_args.kwargs
    assert request["store"] is False
    assert request["text"]["format"]["strict"] is True


def test_missing_model(sanitized_summary, monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    with pytest.raises(ValueError, match="OPENAI_MODEL"):
        analyze_network_health(
            sanitized_summary,
            client=MagicMock(),
        )


def test_api_failure(sanitized_summary):
    client = MagicMock()
    client.responses.create.side_effect = RuntimeError("API unavailable")

    with pytest.raises(NetworkAnalysisError):
        analyze_network_health(
            sanitized_summary,
            client=client,
            model="test-model",
        )


def test_invalid_json(sanitized_summary):
    client = MagicMock()
    client.responses.create.return_value.status = "completed"
    client.responses.create.return_value.output_text = "invalid json"

    with pytest.raises(NetworkAnalysisError):
        analyze_network_health(
            sanitized_summary,
            client=client,
            model="test-model",
        )


def test_incomplete_response(sanitized_summary):
    client = MagicMock()
    client.responses.create.return_value.status = "incomplete"

    with pytest.raises(NetworkAnalysisError):
        analyze_network_health(
            sanitized_summary,
            client=client,
            model="test-model",
        )


def test_empty_response(sanitized_summary):
    client = MagicMock()
    client.responses.create.return_value.status = "completed"
    client.responses.create.return_value.output_text = ""

    with pytest.raises(NetworkAnalysisError):
        analyze_network_health(
            sanitized_summary,
            client=client,
            model="test-model",
        )


def test_rejects_unsanitized_summary(sanitized_summary):
    sanitized_summary["data_quality"][
        "raw_network_addresses_included"
    ] = True

    client = MagicMock()

    with pytest.raises(ValueError):
        analyze_network_health(
            sanitized_summary,
            client=client,
            model="test-model",
        )

    client.responses.create.assert_not_called()
