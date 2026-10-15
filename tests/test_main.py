
"""Tests for the HomeOps-AI main scanning workflow."""

import pytest

import homeops.__main__ as main_module


@pytest.fixture
def mock_network(monkeypatch):
    """Mock the scanner and database to avoid real network access."""

    scanned_devices = [
        {
            "ip_address": "192.168.1.10",
            "mac_address": "AA:BB:CC:DD:EE:01",
            "hostname": "Trusted-PC",
            "vendor": "Example",
            "status": "ONLINE",
            "latency_ms": 5,
            "last_seen": "2026-10-15",
        }
    ]

    database_devices = [
        (
            "192.168.1.10",
            "AA:BB:CC:DD:EE:01",
            "Trusted-PC",
            "Example",
            "2026-10-15",
            "2026-10-15",
            "ONLINE",
            0,
        ),
        (
            "192.168.1.20",
            "AA:BB:CC:DD:EE:02",
            "Offline-PC",
            "Example",
            "2026-10-14",
            "2026-10-14",
            "OFFLINE",
            3,
        ),
    ]

    monkeypatch.setattr(
        main_module,
        "initialize_database",
        lambda: None,
    )

    monkeypatch.setattr(
        main_module,
        "scan_network",
        lambda: scanned_devices,
    )

    monkeypatch.setattr(
        main_module,
        "get_device_by_mac",
        lambda mac: None,
    )

    monkeypatch.setattr(
        main_module,
        "detect_changes",
        lambda previous, current: [],
    )

    monkeypatch.setattr(
        main_module,
        "save_device",
        lambda device: None,
    )

    monkeypatch.setattr(
        main_module,
        "record_scan_history",
        lambda device: None,
    )

    monkeypatch.setattr(
        main_module,
        "get_all_devices",
        lambda: database_devices,
    )

    def unexpected_missed_scan(mac):
        raise AssertionError(
            "Already-offline devices should not "
            "accumulate additional missed scans."
        )

    monkeypatch.setattr(
        main_module,
        "increment_missed_scan",
        unexpected_missed_scan,
    )

    return scanned_devices


def test_unrecognized_device_reported(
    mock_network, monkeypatch, capsys
):
    """The main scanner should report unknown devices."""

    def fake_security_check(devices):
        assert devices == mock_network

        return [
            {
                "hostname": "Unknown-Phone",
                "ip_address": "192.168.1.30",
                "mac_address": "AA:BB:CC:DD:EE:03",
                "status": "UNRECOGNIZED",
            }
        ]

    monkeypatch.setattr(
        main_module,
        "check_unrecognized_devices",
        fake_security_check,
    )

    main_module.main()

    output = capsys.readouterr().out

    assert "Security Review" in output
    assert "Unrecognized devices: 1" in output
    assert "[UNRECOGNIZED DEVICE]" in output
    assert "Unknown-Phone" in output


def test_missing_security_config_does_not_stop_scan(
    mock_network, monkeypatch, capsys
):
    """Missing trusted-device config should not crash scanning."""

    def missing_config(devices):
        raise FileNotFoundError(
            "trusted_devices.json not found"
        )

    monkeypatch.setattr(
        main_module,
        "check_unrecognized_devices",
        missing_config,
    )

    main_module.main()

    output = capsys.readouterr().out

    assert "[SECURITY SKIPPED]" in output
    assert "Scan complete." in output


def test_no_unrecognized_devices(
    mock_network, monkeypatch, capsys
):
    """A clean security check should produce a clean result."""

    monkeypatch.setattr(
        main_module,
        "check_unrecognized_devices",
        lambda devices: [],
    )

    main_module.main()

    output = capsys.readouterr().out

    assert "No unrecognized online devices found." in output
    assert "Scan complete." in output


def test_uppercase_device_status_counts(
    mock_network, monkeypatch, capsys
):
    """ONLINE and OFFLINE statuses should count correctly."""

    monkeypatch.setattr(
        main_module,
        "check_unrecognized_devices",
        lambda devices: [],
    )

    main_module.main()

    output = capsys.readouterr().out

    assert "Known devices: 2" in output
    assert "Online: 1" in output
    assert "Offline: 1" in output
