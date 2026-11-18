"""Dashboard rendering tests for v1.3.0 latency alerts."""

from unittest.mock import patch

from homeops.dashboard import build_dashboard


MAC = "AA:BB:CC:DD:EE:01"


def render_alerts(alerts, unread_count=0):
    """Render dashboard with isolated alert data."""
    with (
        patch("homeops.dashboard.get_all_devices", return_value=[]),
        patch("homeops.dashboard.get_recent_scan_history", return_value=[]),
        patch("homeops.dashboard.get_recent_alerts", return_value=alerts),
        patch("homeops.dashboard.get_unread_alert_count", return_value=unread_count),
        patch("homeops.dashboard.get_device_availability", return_value=[]),
    ):
        return build_dashboard()


def alert(alert_id, alert_type, message, is_read=False):
    return {
        "id": alert_id,
        "alert_type": alert_type,
        "mac_address": MAC,
        "message": message,
        "created_at": "2026-11-18 12:00:00",
        "is_read": is_read,
    }


def test_high_latency_has_warning_label_and_style():
    html = render_alerts([alert(1, "HIGH_LATENCY", "Latency spiked to 180 ms")], 1)
    assert "High Latency Detected" in html
    assert '<span class="alert-badge alert-latency">' in html
    assert "Latency spiked to 180 ms" in html
    assert MAC in html


def test_latency_recovered_has_recovery_label_and_style():
    html = render_alerts([alert(2, "LATENCY_RECOVERED", "Latency returned to normal", True)])
    assert "Latency Recovered" in html
    assert '<span class="alert-badge alert-recovery">' in html
    assert "Latency returned to normal" in html
    assert '<span class="read-status">Read</span>' in html
    assert 'action="/alerts/read"' not in html


def test_latency_alerts_preserve_unread_action():
    html = render_alerts([alert(3, "HIGH_LATENCY", "Latency elevated")], 1)
    assert 'action="/alerts/read"' in html
    assert 'value="3"' in html
    assert "Mark as Read" in html
    assert 'class="unread-alert"' in html


def test_latency_messages_are_html_escaped():
    html = render_alerts([alert(4, "HIGH_LATENCY", "<script>alert(1)</script>")])
    assert "&lt;script&gt;" in html
    assert "<script>alert(1)</script>" not in html


def test_existing_alert_types_still_render():
    html = render_alerts([
        alert(5, "NEW_DEVICE", "New device"),
        alert(6, "DEVICE_OFFLINE", "Device offline"),
        alert(7, "DEVICE_ONLINE", "Device reconnected"),
    ])
    assert "Security Alert" in html
    assert "Device Offline" in html
    assert "Device Reconnected" in html
    assert '<span class="alert-badge alert-security">' in html
    assert '<span class="alert-badge alert-offline">' in html
    assert '<span class="alert-badge alert-recovery">' in html
