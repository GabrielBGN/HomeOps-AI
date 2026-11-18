"""Tests for safe AI report HTML rendering."""

import pytest

from homeops.ai_analyst import NetworkAnalysisError
from homeops.ai_report_view import render_ai_report


def sample_report():
    return {
        "overall_health": "HEALTHY",
        "severity": "LOW",
        "executive_summary": "Network operating normally.",
        "findings": ["All monitored devices are online."],
        "recommendations": ["Continue monitoring."],
        "limitations": ["Limited observation window."],
    }


def test_report_renders_expected_sections():
    html = render_ai_report(sample_report())

    assert "AI Network Analysis" in html
    assert "HEALTHY" in html
    assert "Network operating normally." in html
    assert "Continue monitoring." in html


def test_report_escapes_untrusted_html():
    report = sample_report()
    report["executive_summary"] = "<script>alert(1)</script>"
    report["findings"] = ["<img src=x onerror=alert(1)>"]

    html = render_ai_report(report)

    assert "<script>" not in html
    assert "<img" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;img" in html


def test_report_rejects_invalid_schema():
    report = sample_report()
    report["severity"] = "EXTREME"

    with pytest.raises(NetworkAnalysisError):
        render_ai_report(report)
