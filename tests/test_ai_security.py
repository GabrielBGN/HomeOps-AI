"""Security regression tests for the HomeOps-AI network analyst."""

import copy

import pytest

from homeops.ai_analyst import (
    NetworkAnalysisError,
    build_network_health_summary,
    validate_ai_report,
    validate_network_summary,
)


@pytest.fixture
def safe_summary():
    return build_network_health_summary(
        devices=[],
        availability=[],
        alerts=[],
        scan_history=[],
        latency_histories={},
    )


@pytest.fixture
def valid_report():
    return {
        "overall_health": "HEALTHY",
        "severity": "LOW",
        "executive_summary": "No connectivity issues observed.",
        "findings": [],
        "recommendations": [],
        "limitations": ["Limited historical data."],
    }


def test_valid_summary_accepted(safe_summary):
    validate_network_summary(safe_summary)


def test_raw_ip_field_rejected(safe_summary):
    summary = copy.deepcopy(safe_summary)
    summary["ip_address"] = "192.168.1.100"

    with pytest.raises(ValueError):
        validate_network_summary(summary)


def test_raw_hostname_field_rejected(safe_summary):
    summary = copy.deepcopy(safe_summary)
    summary["hostname"] = "Private-Laptop"

    with pytest.raises(ValueError):
        validate_network_summary(summary)


def test_privacy_flag_cannot_be_disabled(safe_summary):
    summary = copy.deepcopy(safe_summary)
    summary["data_quality"]["raw_network_addresses_included"] = True

    with pytest.raises(ValueError):
        validate_network_summary(summary)


def test_alert_messages_cannot_be_enabled(safe_summary):
    summary = copy.deepcopy(safe_summary)
    summary["data_quality"]["alert_messages_included"] = True

    with pytest.raises(ValueError):
        validate_network_summary(summary)


def test_sensitive_alert_type_removed():
    summary = build_network_health_summary(
        devices=[],
        availability=[],
        alerts=[
            {
                "alert_type": "DEVICE_OFFLINE_192.168.1.50",
                "message": "Private network information",
                "is_read": False,
            }
        ],
        scan_history=[],
        latency_histories={},
    )

    assert summary["alerts"]["by_type"] == {"UNKNOWN": 1}
    assert "192.168.1.50" not in str(summary)
    assert "Private network information" not in str(summary)


def test_valid_ai_report_accepted(valid_report):
    assert validate_ai_report(valid_report) == valid_report


def test_invalid_health_status_rejected(valid_report):
    report = copy.deepcopy(valid_report)
    report["overall_health"] = "BANANA"

    with pytest.raises(NetworkAnalysisError):
        validate_ai_report(report)


def test_invalid_severity_rejected(valid_report):
    report = copy.deepcopy(valid_report)
    report["severity"] = "SUPER_HIGH"

    with pytest.raises(NetworkAnalysisError):
        validate_ai_report(report)


def test_unexpected_ai_field_rejected(valid_report):
    report = copy.deepcopy(valid_report)
    report["private_data"] = "Unexpected content"

    with pytest.raises(NetworkAnalysisError):
        validate_ai_report(report)


def test_missing_ai_field_rejected(valid_report):
    report = copy.deepcopy(valid_report)
    del report["recommendations"]

    with pytest.raises(NetworkAnalysisError):
        validate_ai_report(report)


def test_invalid_findings_rejected(valid_report):
    report = copy.deepcopy(valid_report)
    report["findings"] = ["Valid finding", 123]

    with pytest.raises(NetworkAnalysisError):
        validate_ai_report(report)


def test_empty_executive_summary_rejected(valid_report):
    report = copy.deepcopy(valid_report)
    report["executive_summary"] = "   "

    with pytest.raises(NetworkAnalysisError):
        validate_ai_report(report)
