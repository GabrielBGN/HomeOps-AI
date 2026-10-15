
"""Tests for HomeOps-AI offline detection."""

import pytest

import homeops.__main__ as main_module


@pytest.fixture
def mock_environment(monkeypatch):
    """Set up a simulated network and database."""

    events = {
        "missed": [],
        "offline": [],
        "history": [],
    }

    known_device = (
        "192.168.1.50",
        "AA:BB:CC:DD:EE:50",
        "Test-PC",
        "Example Vendor",
        "2026-10-01",
        "2026-10-15",
        "ONLINE",
        0,
    )

    monkeypatch.setattr(
        main_module,
        "initialize_database",
        lambda: None,
    )

    # Simulate a scan where no devices respond.
    monkeypatch.setattr(
        main_module,
        "scan_network",
        lambda: [],
    )

    monkeypatch.setattr(
        main_module,
        "get_all_devices",
        lambda: [known_device],
    )

    monkeypatch.setattr(
        main_module,
        "detect_changes",
        lambda previous, current: [],
    )

    monkeypatch.setattr(
        main_module,
        "record_scan_history",
        lambda device: events["history"].append(device),
    )

    monkeypatch.setattr(
        main_module,
        "mark_device_offline",
        lambda mac: events["offline"].append(mac),
    )

    monkeypatch.setattr(
        main_module,
        "check_unrecognized_devices",
        lambda devices: [],
    )

    return events, known_device


def test_two_missed_scans_stays_online(
    mock_environment, monkeypatch
):
    """Two missed scans must not mark a device offline."""

    events, device = mock_environment

    def increment(mac):
        events["missed"].append(mac)
        return 2

    monkeypatch.setattr(
        main_module,
        "increment_missed_scan",
        increment,
    )

    main_module.main()

    assert events["missed"] == [device[1]]
    assert events["offline"] == []
    assert events["history"] == []


def test_three_missed_scans_marks_offline(
    mock_environment, monkeypatch
):
    """Three missed scans must trigger offline detection."""

    events, device = mock_environment

    def increment(mac):
        events["missed"].append(mac)
        return 3

    monkeypatch.setattr(
        main_module,
        "increment_missed_scan",
        increment,
    )

    main_module.main()

    assert events["offline"] == [device[1]]

    assert len(events["history"]) == 1
    assert events["history"][0]["status"] == "OFFLINE"
    assert events["history"][0]["mac_address"] == device[1]


def test_already_offline_device_is_skipped(
    mock_environment, monkeypatch
):
    """Offline devices should not accumulate missed scans."""

    events, device = mock_environment

    offline_device = (
        device[0],
        device[1],
        device[2],
        device[3],
        device[4],
        device[5],
        "OFFLINE",
        3,
    )

    monkeypatch.setattr(
        main_module,
        "get_all_devices",
        lambda: [offline_device],
    )

    def unexpected_increment(mac):
        raise AssertionError(
            "Already-offline device was counted again."
        )

    monkeypatch.setattr(
        main_module,
        "increment_missed_scan",
        unexpected_increment,
    )

    main_module.main()

    assert events["offline"] == []
    assert events["history"] == []
