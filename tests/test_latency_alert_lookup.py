"""SQLite tests for the latest per-device latency incident alert."""

import pytest

from homeops import database


@pytest.fixture
def alert_database(tmp_path, monkeypatch):
    """Use an isolated database rather than the HomeOps-AI live database."""
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "alerts.db")
    database.initialize_database()
    return database


def test_no_latency_alert_returns_none(alert_database):
    assert alert_database.get_latest_latency_alert("AA:BB:CC:DD:EE:01") is None


def test_returns_latest_latency_alert(alert_database):
    mac = "AA:BB:CC:DD:EE:01"
    first_id = alert_database.create_alert("HIGH_LATENCY", mac, "Spike detected")
    recovery_id = alert_database.create_alert("LATENCY_RECOVERED", mac, "Recovered")

    result = alert_database.get_latest_latency_alert(mac)
    assert result["id"] == recovery_id
    assert result["id"] > first_id
    assert result["alert_type"] == "LATENCY_RECOVERED"
    assert result["mac_address"] == mac
    assert result["message"] == "Recovered"
    assert result["is_read"] is False


def test_ignores_unrelated_alert_types(alert_database):
    mac = "AA:BB:CC:DD:EE:01"
    latency_id = alert_database.create_alert("HIGH_LATENCY", mac, "High latency")
    alert_database.create_alert("DEVICE_OFFLINE", mac, "Offline")
    alert_database.create_alert("NEW_DEVICE", mac, "New device")

    result = alert_database.get_latest_latency_alert(mac)
    assert result["id"] == latency_id
    assert result["alert_type"] == "HIGH_LATENCY"


def test_alerts_are_isolated_by_mac_address(alert_database):
    first_mac = "AA:BB:CC:DD:EE:01"
    second_mac = "AA:BB:CC:DD:EE:02"
    first_id = alert_database.create_alert("HIGH_LATENCY", first_mac, "First device")
    alert_database.create_alert("LATENCY_RECOVERED", second_mac, "Second device")

    result = alert_database.get_latest_latency_alert(first_mac)
    assert result["id"] == first_id
    assert alert_database.get_latest_latency_alert("AA:BB:CC:DD:EE:03") is None


def test_read_status_does_not_change_incident_state(alert_database):
    mac = "AA:BB:CC:DD:EE:01"
    alert_id = alert_database.create_alert("HIGH_LATENCY", mac, "Spike")
    assert alert_database.mark_alert_read(alert_id) is True

    result = alert_database.get_latest_latency_alert(mac)
    assert result["id"] == alert_id
    assert result["alert_type"] == "HIGH_LATENCY"
    assert result["is_read"] is True
