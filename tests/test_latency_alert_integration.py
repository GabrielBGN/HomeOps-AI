"""Integration tests for persistent latency incidents in the main scan workflow."""

import pytest

import homeops.__main__ as main_module


MAC = "AA:BB:CC:DD:EE:01"


@pytest.fixture
def scan_harness(monkeypatch):
    """Simulate scans and an in-memory sequence of latency-related alerts."""
    state = {
        "latency": 10.0,
        "history": [10.0, 11.0, 9.0, 10.0, 10.0],
        "alerts": [],
        "events": [],
        "known": True,
    }

    def scanned_devices():
        return [{
            "ip_address": "192.168.1.10",
            "mac_address": MAC,
            "hostname": "Test-PC",
            "vendor": "Example",
            "status": "ONLINE",
            "latency_ms": state["latency"],
            "last_seen": "2026-11-18T12:00:00",
        }]

    def previous_device(mac):
        assert mac == MAC
        return {"mac_address": MAC, "status": "ONLINE"} if state["known"] else None

    def history(mac):
        assert mac == MAC
        state["events"].append("history_lookup")
        return list(state["history"])

    def latest_alert(mac):
        assert mac == MAC
        state["events"].append("alert_lookup")
        return next(
            (alert for alert in reversed(state["alerts"])
             if alert["alert_type"] in ("HIGH_LATENCY", "LATENCY_RECOVERED")),
            None,
        )

    def create_alert(alert_type, mac, message):
        assert mac == MAC
        state["events"].append("create_alert")
        state["alerts"].append({
            "alert_type": alert_type,
            "mac_address": mac,
            "message": message,
        })
        return len(state["alerts"])

    def record_observation(mac, observed_status, confirmed_status, latency_ms=None):
        assert mac == MAC
        assert observed_status == "SEEN"
        assert confirmed_status == "ONLINE"
        state["events"].append("record_observation")
        return True

    monkeypatch.setattr(main_module, "initialize_database", lambda: None)
    monkeypatch.setattr(main_module, "scan_network", scanned_devices)
    monkeypatch.setattr(main_module, "get_device_by_mac", previous_device)
    monkeypatch.setattr(main_module, "detect_changes", lambda old, new: [])
    monkeypatch.setattr(main_module, "get_device_latency_history", history)
    monkeypatch.setattr(main_module, "get_latest_latency_alert", latest_alert)
    monkeypatch.setattr(main_module, "create_alert", create_alert)
    monkeypatch.setattr(main_module, "save_device", lambda device: None)
    monkeypatch.setattr(main_module, "record_scan_history", lambda device: None)
    monkeypatch.setattr(main_module, "record_scan_observation", record_observation)
    monkeypatch.setattr(
        main_module,
        "get_all_devices",
        lambda: [("192.168.1.10", MAC, "Test-PC", "Example",
                  "2026-11-18", "2026-11-18", "ONLINE", 0)],
    )
    monkeypatch.setattr(main_module, "check_unrecognized_devices", lambda devices: [])
    monkeypatch.setattr(main_module, "load_trusted_macs", lambda: {MAC})
    return state


def test_new_spike_creates_persistent_alert(scan_harness, capsys):
    scan_harness["latency"] = 120.0
    main_module.main()
    output = capsys.readouterr().out
    assert "[ANOMALY]" in output
    assert "[ALERT] High latency" in output
    assert [a["alert_type"] for a in scan_harness["alerts"]] == ["HIGH_LATENCY"]
    assert scan_harness["events"].index("history_lookup") < scan_harness["events"].index("record_observation")
    assert scan_harness["events"].index("create_alert") < scan_harness["events"].index("record_observation")


def test_ongoing_spike_does_not_duplicate_alert(scan_harness):
    scan_harness["latency"] = 120.0
    main_module.main()
    main_module.main()
    assert [a["alert_type"] for a in scan_harness["alerts"]] == ["HIGH_LATENCY"]


def test_recovery_creates_one_recovery_alert(scan_harness, capsys):
    scan_harness["latency"] = 120.0
    main_module.main()
    scan_harness["latency"] = 10.0
    main_module.main()
    main_module.main()
    output = capsys.readouterr().out
    assert "latency recovered" in output
    assert [a["alert_type"] for a in scan_harness["alerts"]] == [
        "HIGH_LATENCY", "LATENCY_RECOVERED"
    ]


def test_insufficient_history_does_not_change_incident(scan_harness):
    scan_harness["latency"] = 120.0
    main_module.main()
    scan_harness["history"] = [10.0, 11.0]
    scan_harness["latency"] = 10.0
    main_module.main()
    assert [a["alert_type"] for a in scan_harness["alerts"]] == ["HIGH_LATENCY"]


def test_invalid_current_latency_does_not_close_incident(scan_harness):
    scan_harness["latency"] = 120.0
    main_module.main()
    scan_harness["latency"] = None
    main_module.main()
    assert [a["alert_type"] for a in scan_harness["alerts"]] == ["HIGH_LATENCY"]


def test_new_device_does_not_attempt_history_or_alert(scan_harness):
    scan_harness["known"] = False
    scan_harness["latency"] = 120.0
    main_module.main()
    assert scan_harness["alerts"] == []
    assert "history_lookup" not in scan_harness["events"]
    assert "alert_lookup" not in scan_harness["events"]
