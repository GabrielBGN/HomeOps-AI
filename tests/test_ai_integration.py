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
    return {
        "report_type": "network_health_summary",
        "device_totals": {
            "total": 2,
            "online": 1,
            "offline": 1,
            "other": 0,
        },
        "devices": [],
        "alerts": {"total": 0, "unread": 0, "by_type": {}},
        "recent_scans": {"records_analyzed": 0},
        "data_quality": {
            "raw_network_addresses_included": False,
            "alert_messages_included": False,
        },
    }


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
