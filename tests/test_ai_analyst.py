
from homeops.ai_analyst import build_network_health_summary


def test_build_network_health_summary():
    devices = [
        (
            "192.168.1.10",
            "AA:BB:CC:DD:EE:01",
            "Gaming-PC",
            "Example Vendor",
            "2026-11-01",
            "2026-11-18",
            "ONLINE",
            0,
        ),
        (
            "192.168.1.20",
            "AA:BB:CC:DD:EE:02",
            "Smart-TV",
            "Example Vendor",
            "2026-11-01",
            "2026-11-18",
            "OFFLINE",
            3,
        ),
    ]

    availability = [
        {
            "mac_address": "AA:BB:CC:DD:EE:01",
            "availability_pct": 98.5,
            "total_observations": 200,
            "seen_count": 197,
            "missed_count": 3,
        }
    ]

    alerts = [
        {
            "alert_type": "DEVICE_OFFLINE",
            "message": "Private network information",
            "is_read": False,
        },
        {
            "alert_type": "NEW_DEVICE",
            "message": "Another private message",
            "is_read": True,
        },
    ]

    scan_history = [
        {"status": "ONLINE", "latency_ms": 10.0},
        {"status": "ONLINE", "latency_ms": 20.0},
        {"status": "OFFLINE", "latency_ms": None},
    ]

    latency_histories = {
        "AA:BB:CC:DD:EE:01": [10.0, 20.0, 30.0],
        "AA:BB:CC:DD:EE:02": [],
    }

    summary = build_network_health_summary(
        devices,
        availability,
        alerts,
        scan_history,
        latency_histories,
    )

    assert summary["device_totals"]["total"] == 2
    assert summary["device_totals"]["online"] == 1
    assert summary["device_totals"]["offline"] == 1

    assert summary["devices"][0]["device_id"] == "Device-001"
    assert summary["devices"][0]["availability"]["percentage"] == 98.5

    assert summary["devices"][0]["latency"]["average_ms"] == 20.0
    assert summary["devices"][0]["latency"]["median_ms"] == 20.0
    assert summary["devices"][0]["latency"]["maximum_ms"] == 30.0

    assert summary["alerts"]["total"] == 2
    assert summary["alerts"]["unread"] == 1

    assert summary["recent_scans"]["records_analyzed"] == 3
    assert summary["recent_scans"]["latency"]["sample_count"] == 2

    assert summary["data_quality"]["raw_network_addresses_included"] is False


def test_summary_does_not_expose_sensitive_information():
    devices = [
        (
            "192.168.1.99",
            "AA:BB:CC:DD:EE:99",
            "Private-Computer",
            "Private Vendor",
            "2026-11-01",
            "2026-11-18",
            "ONLINE",
            0,
        )
    ]

    alerts = [
        {
            "alert_type": "NEW_DEVICE",
            "message": "Sensitive private alert",
            "is_read": False,
        }
    ]

    summary = build_network_health_summary(
        devices=devices,
        availability=[],
        alerts=alerts,
        scan_history=[],
        latency_histories={},
    )

    summary_text = str(summary)

    sensitive_values = [
        "192.168.1.99",
        "AA:BB:CC:DD:EE:99",
        "Private-Computer",
        "Private Vendor",
        "Sensitive private alert",
    ]

    for value in sensitive_values:
        assert value not in summary_text


def test_empty_network_summary():
    summary = build_network_health_summary(
        devices=[],
        availability=[],
        alerts=[],
        scan_history=[],
        latency_histories={},
    )

    assert summary["device_totals"]["total"] == 0
    assert summary["device_totals"]["online"] == 0
    assert summary["device_totals"]["offline"] == 0
    assert summary["alerts"]["total"] == 0
    assert summary["recent_scans"]["records_analyzed"] == 0
    assert summary["recent_scans"]["latency"]["average_ms"] is None


def test_latency_summary_ignores_invalid_samples():
    summary = build_network_health_summary(
        devices=[
            (
                "192.168.1.10",
                "AA:BB:CC:DD:EE:01",
                "Gaming-PC",
                "Vendor",
                "2026-11-01",
                "2026-11-18",
                "ONLINE",
                0,
            )
        ],
        availability=[],
        alerts=[],
        scan_history=[],
        latency_histories={
            "AA:BB:CC:DD:EE:01": [10.0, -5.0, float("nan"), None, 30.0]
        },
    )

    latency = summary["devices"][0]["latency"]

    assert latency["sample_count"] == 2
    assert latency["average_ms"] == 20.0
    assert latency["maximum_ms"] == 30.0

