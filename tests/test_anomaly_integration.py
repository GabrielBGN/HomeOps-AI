"""Integration tests for latency anomaly detection in the main scan workflow."""

import pytest

import homeops.__main__ as main_module


MAC = "AA:BB:CC:DD:EE:01"
BASELINE = [9.0, 10.0, 11.0, 10.0, 10.0]


@pytest.fixture
def scan_environment(monkeypatch):
    """Simulate a known online device without network or SQLite access."""
    current_device = {
        "ip_address": "192.168.1.10",
        "mac_address": MAC,
        "hostname": "Trusted-PC",
        "vendor": "Example",
        "status": "ONLINE",
        "latency_ms": 10.0,
        "last_seen": "2026-10-15",
    }
    previous_device = dict(current_device)
    inventory = [
        (
            current_device["ip_address"],
            MAC,
            current_device["hostname"],
            current_device["vendor"],
            "2026-10-01",
            current_device["last_seen"],
            "ONLINE",
            0,
        )
    ]
    events = []
    history = list(BASELINE)

    monkeypatch.setattr(main_module, "initialize_database", lambda: None)
    monkeypatch.setattr(main_module, "scan_network", lambda: [current_device])
    monkeypatch.setattr(main_module, "get_device_by_mac", lambda mac: previous_device if mac == MAC else None)
    monkeypatch.setattr(main_module, "detect_changes", lambda old, new: [])
    monkeypatch.setattr(main_module, "save_device", lambda device: events.append("save_device"))
    monkeypatch.setattr(main_module, "record_scan_history", lambda device: events.append("scan_history"))

    def record_observation(mac, observed_status, confirmed_status, latency_ms=None):
        assert mac == MAC
        assert observed_status == "SEEN"
        assert confirmed_status == "ONLINE"
        events.append("observation")
        return True

    def get_history(mac, *args, **kwargs):
        assert mac == MAC
        events.append("history_lookup")
        return list(history)

    monkeypatch.setattr(main_module, "record_scan_observation", record_observation)
    monkeypatch.setattr(main_module, "get_device_latency_history", get_history)
    monkeypatch.setattr(main_module, "get_all_devices", lambda: inventory)
    monkeypatch.setattr(main_module, "check_unrecognized_devices", lambda devices: [])
    monkeypatch.setattr(main_module, "create_network_alerts", lambda *args, **kwargs: events.append("network_alerts"))

    return current_device, history, events


def test_normal_latency_does_not_log_anomaly(scan_environment, capsys):
    device, history, events = scan_environment
    device["latency_ms"] = 12.0

    main_module.main()

    output = capsys.readouterr().out
    assert "[ANOMALY]" not in output
    assert "Scan complete." in output
    assert "observation" in events


def test_high_latency_logs_anomaly(scan_environment, capsys):
    device, history, events = scan_environment
    device["latency_ms"] = 150.0

    main_module.main()

    output = capsys.readouterr().out
    assert "[ANOMALY]" in output
    assert "Trusted-PC" in output
    assert MAC in output
    assert "150.0 ms" in output
    assert "observation" in events
    assert "network_alerts" in events


def test_insufficient_history_does_not_log_anomaly(scan_environment, capsys):
    device, history, events = scan_environment
    device["latency_ms"] = 150.0
    history[:] = [10.0, 11.0]

    main_module.main()

    output = capsys.readouterr().out
    assert "[ANOMALY]" not in output
    assert "Scan complete." in output


def test_history_lookup_precedes_current_observation(scan_environment):
    device, history, events = scan_environment
    device["latency_ms"] = 150.0

    main_module.main()

    assert events.index("history_lookup") < events.index("observation")
    assert events.count("history_lookup") == 1
    assert events.count("observation") == 1
    assert history == BASELINE  # The current reading is not added to the baseline.
