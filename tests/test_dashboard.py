
from unittest.mock import patch

from homeops.dashboard import build_dashboard


def render_dashboard(devices, history):
    """Generate dashboard HTML using fake test data."""

    with patch(
        "homeops.dashboard.get_all_devices",
        return_value=devices
    ), patch(
        "homeops.dashboard.get_recent_scan_history",
        return_value=history
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
    assert "Total Devices" in html


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
