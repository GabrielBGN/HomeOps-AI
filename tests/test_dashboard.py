
"""Tests for the HomeOps-AI dashboard."""

from unittest.mock import patch

from homeops.dashboard import build_dashboard


def render_dashboard(devices, history, alerts=None, unread_count=0):
    """Generate dashboard HTML using fake test data."""

    if alerts is None:
        alerts = []

    with patch(
        "homeops.dashboard.get_all_devices",
        return_value=devices,
    ), patch(
        "homeops.dashboard.get_recent_scan_history",
        return_value=history,
    ), patch(
        "homeops.dashboard.get_recent_alerts",
        return_value=alerts,
    ), patch(
        "homeops.dashboard.get_unread_alert_count",
        return_value=unread_count,
    ):
        return build_dashboard()


def test_dashboard_displays_devices():
    devices = [
        (
            "192.168.1.10",
            "AA:BB:CC:DD:EE:01",
            "Gaming-PC",
            "Example Vendor",
            "2026-10-15 10:00:00",
            "2026-10-15 10:05:00",
            "ONLINE",
            0,
        ),
        (
            "192.168.1.20",
            "AA:BB:CC:DD:EE:02",
            "Smart-TV",
            "Example Vendor",
            "2026-10-15 10:00:00",
            "2026-10-15 10:00:00",
            "OFFLINE",
            3,
        ),
    ]

    html = render_dashboard(devices, [])

    assert "Gaming-PC" in html
    assert "Smart-TV" in html
    assert "192.168.1.10" in html
    assert "192.168.1.20" in html
    assert "ONLINE" in html
    assert "OFFLINE" in html
    assert "Total Devices" in html


def test_dashboard_displays_scan_history():
    history = [
        {
            "hostname": "Gaming-PC",
            "ip_address": "192.168.1.10",
            "status": "ONLINE",
            "latency_ms": 2.4,
            "timestamp": "2026-10-15 10:05:00",
        }
    ]

    html = render_dashboard([], history)

    assert "Recent Scan History" in html
    assert "Gaming-PC" in html
    assert "2.4 ms" in html
    assert "2026-10-15 10:05:00" in html


def test_dashboard_handles_empty_database():
    html = render_dashboard([], [])

    assert "No devices discovered yet." in html
    assert "No scan history available." in html
    assert "No network alerts recorded yet." in html
    assert "Total Devices" in html
    assert "Unread Alerts" in html


def test_dashboard_escapes_html():
    devices = [
        (
            "192.168.1.30",
            "AA:BB:CC:DD:EE:03",
            "<script>alert(1)</script>",
            "Unknown",
            None,
            None,
            "ONLINE",
            0,
        )
    ]

    html = render_dashboard(devices, [])

    assert "&lt;script&gt;" in html
    assert "<script>alert(1)</script>" not in html


def test_dashboard_displays_unread_alert():
    alerts = [
        {
            "id": 1,
            "alert_type": "NEW_DEVICE",
            "mac_address": "AA:BB:CC:DD:EE:99",
            "message": "Unrecognized device detected.",
            "created_at": "2026-10-21 10:00:00",
            "is_read": False,
        }
    ]

    html = render_dashboard(
        [],
        [],
        alerts=alerts,
        unread_count=1,
    )

    assert "Network Alerts" in html
    assert "Security Alert" in html
    assert "Unrecognized device detected." in html
    assert "AA:BB:CC:DD:EE:99" in html
    assert "Unread Alerts" in html
    assert "Mark as Read" in html
    assert 'value="1"' in html


def test_dashboard_displays_read_alert():
    alerts = [
        {
            "id": 2,
            "alert_type": "DEVICE_OFFLINE",
            "mac_address": "AA:BB:CC:DD:EE:01",
            "message": "Gaming-PC went offline.",
            "created_at": "2026-10-21 10:05:00",
            "is_read": True,
        }
    ]

    html = render_dashboard(
        [],
        [],
        alerts=alerts,
        unread_count=0,
    )

    assert "Device Offline" in html
    assert "Gaming-PC went offline." in html
    assert "read-alert" in html
    assert '<span class="read-status">Read</span>' in html
    assert 'action="/alerts/read"' not in html


def test_dashboard_displays_reconnection_alert():
    alerts = [
        {
            "id": 3,
            "alert_type": "DEVICE_ONLINE",
            "mac_address": "AA:BB:CC:DD:EE:01",
            "message": "Gaming-PC reconnected.",
            "created_at": "2026-10-21 10:10:00",
            "is_read": False,
        }
    ]

    html = render_dashboard(
        [],
        [],
        alerts=alerts,
        unread_count=1,
    )

    assert "Device Reconnected" in html
    assert "Gaming-PC reconnected." in html
    assert "alert-recovery" in html


def test_dashboard_escapes_alert_messages():
    alerts = [
        {
            "id": 4,
            "alert_type": "NEW_DEVICE",
            "mac_address": "AA:BB:CC:DD:EE:04",
            "message": "<script>alert('unsafe')</script>",
            "created_at": "2026-10-21 10:15:00",
            "is_read": False,
        }
    ]

    html = render_dashboard(
        [],
        [],
        alerts=alerts,
        unread_count=1,
    )

    assert "&lt;script&gt;" in html
    assert "<script>alert('unsafe')</script>" not in html
