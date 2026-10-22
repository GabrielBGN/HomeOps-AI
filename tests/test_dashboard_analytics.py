"""Tests for HomeOps-AI v1.2.0 dashboard analytics."""

from unittest.mock import patch

import pytest

from homeops.dashboard import build_dashboard


def render_analytics(availability):
    """Render dashboard with isolated analytics and empty other sections."""
    with (
        patch("homeops.dashboard.get_all_devices", return_value=[]),
        patch("homeops.dashboard.get_recent_scan_history", return_value=[]),
        patch("homeops.dashboard.get_recent_alerts", return_value=[]),
        patch("homeops.dashboard.get_unread_alert_count", return_value=0),
        patch("homeops.dashboard.get_device_availability", return_value=availability),
    ):
        return build_dashboard()


def device(*, hostname="Laptop", ip="192.168.1.10", status="ONLINE",
           seen=0, missed=0, availability_pct=None):
    """Create an analytics record matching get_device_availability()."""
    return {
        "mac_address": "AA:BB:CC:DD:EE:10",
        "hostname": hostname,
        "ip_address": ip,
        "status": status,
        "total_observations": seen + missed,
        "seen_count": seen,
        "missed_count": missed,
        "availability_pct": availability_pct,
    }


@pytest.mark.parametrize(
    ("seen", "missed", "percentage", "expected"),
    [
        (4, 0, 100.0, "100.00%"),
        (2, 2, 50.0, "50.00%"),
        (0, 4, 0.0, "0.00%"),
    ],
)
def test_displays_availability_percentages(seen, missed, percentage, expected):
    html = render_analytics([
        device(seen=seen, missed=missed, availability_pct=percentage)
    ])

    assert "Network Analytics: Device Availability" in html
    assert expected in html
    assert "Laptop" in html
    assert "192.168.1.10" in html


def test_displays_na_without_observations():
    html = render_analytics([device()])

    assert "Observed Availability" in html
    assert "<td>N/A</td>" in html
    assert "N/A means no observations" in html


def test_displays_counts_and_current_status():
    html = render_analytics([
        device(status="OFFLINE", seen=3, missed=7, availability_pct=30.0)
    ])

    assert '<span class="offline">OFFLINE</span>' in html
    assert "30.00%" in html
    assert "<td>3</td>" in html
    assert "<td>7</td>" in html
    assert "<td>10</td>" in html


def test_displays_multiple_devices():
    html = render_analytics([
        device(hostname="Laptop", seen=3, missed=1, availability_pct=75.0),
        device(hostname="Desktop", ip="192.168.1.20", status="OFFLINE",
               seen=1, missed=3, availability_pct=25.0),
    ])

    assert "Laptop" in html
    assert "Desktop" in html
    assert "75.00%" in html
    assert "25.00%" in html
    assert "192.168.1.20" in html


def test_empty_analytics_preserves_dashboard_sections():
    html = render_analytics([])

    assert "Network Analytics: Device Availability" in html
    assert "No devices discovered yet." in html
    assert "Network Alerts" in html
    assert "Network Inventory" in html
    assert "Recent Scan History" in html


def test_analytics_escapes_untrusted_device_values():
    html = render_analytics([
        device(hostname="<script>alert(1)</script>",
               ip="<img src=x onerror=alert(1)>",
               seen=1, availability_pct=100.0)
    ])

    assert "&lt;script&gt;" in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html
    assert "<script>alert(1)</script>" not in html
    assert "<img src=x onerror=alert(1)>" not in html
