
"""Tests for the HomeOps-AI network security audit."""

import pytest

from homeops import audit


@pytest.fixture
def sample_devices():
    """Simulated devices from the SQLite inventory."""

    return [
        (
            "192.168.1.10",
            "AA:BB:CC:DD:EE:01",
            "Gaming-PC",
            "Example Vendor",
            None,
            None,
            "ONLINE",
            0,
        ),
        (
            "192.168.1.20",
            "AA:BB:CC:DD:EE:02",
            "Unknown-Phone",
            "Example Vendor",
            None,
            None,
            "ONLINE",
            0,
        ),
        (
            "192.168.1.30",
            "AA:BB:CC:DD:EE:03",
            "Old-Laptop",
            "Example Vendor",
            None,
            None,
            "OFFLINE",
            3,
        ),
        (
            "192.168.1.40",
            None,
            "Unidentified-Device",
            None,
            None,
            None,
            "ONLINE",
            0,
        ),
    ]


def test_audit_device_counts(sample_devices):
    """Audit should calculate accurate device counts."""

    results = audit.audit_devices(
        sample_devices,
        {"AA:BB:CC:DD:EE:01"},
    )

    assert results["total"] == 4
    assert results["online"] == 3
    assert results["offline"] == 1
    assert results["trusted_online"] == 1
    assert results["unrecognized_online"] == 1
    assert results["unverifiable_online"] == 1


def test_trusted_device_recognized(sample_devices):
    """A trusted MAC address should be classified correctly."""

    results = audit.audit_devices(
        sample_devices,
        {"aa-bb-cc-dd-ee-01"},
    )

    gaming_pc = results["devices"][0]

    assert gaming_pc["hostname"] == "Gaming-PC"
    assert gaming_pc["trust_status"] == "TRUSTED"


def test_unrecognized_online_device(sample_devices):
    """An unknown online MAC should require review."""

    results = audit.audit_devices(
        sample_devices,
        {"AA:BB:CC:DD:EE:01"},
    )

    unknown_phone = results["devices"][1]

    assert unknown_phone["status"] == "ONLINE"
    assert unknown_phone["trust_status"] == "UNRECOGNIZED"


def test_offline_device_not_active_alert(sample_devices):
    """Offline devices should not count as active alerts."""

    results = audit.audit_devices(
        sample_devices,
        {"AA:BB:CC:DD:EE:01"},
    )

    old_laptop = results["devices"][2]

    assert old_laptop["status"] == "OFFLINE"
    assert old_laptop["trust_status"] == "UNRECOGNIZED"

    assert results["unrecognized_online"] == 1


def test_missing_mac_is_unverifiable(sample_devices):
    """Devices without valid MACs should be unverifiable."""

    results = audit.audit_devices(
        sample_devices,
        {"AA:BB:CC:DD:EE:01"},
    )

    unidentified = results["devices"][3]

    assert unidentified["mac_address"] is None
    assert unidentified["trust_status"] == "UNVERIFIABLE"
    assert results["unverifiable_online"] == 1


def test_empty_inventory():
    """An empty database should produce zero counts."""

    results = audit.audit_devices(
        [],
        set(),
    )

    assert results["total"] == 0
    assert results["online"] == 0
    assert results["offline"] == 0
    assert results["unrecognized_online"] == 0
    assert results["devices"] == []


def test_report_shows_devices_requiring_review(
    sample_devices, capsys
):
    """The report should identify online devices needing review."""

    results = audit.audit_devices(
        sample_devices,
        {"AA:BB:CC:DD:EE:01"},
    )

    audit.print_audit_report(results)

    output = capsys.readouterr().out

    assert "Network Security Audit" in output
    assert "Unknown-Phone" in output
    assert "Unidentified-Device" in output
    assert "[UNRECOGNIZED]" in output
    assert "[UNVERIFIABLE]" in output

    # Offline devices should not appear in the review section.
    review_section = output.split(
        "Devices Requiring Review"
    )[1]

    assert "Old-Laptop" not in review_section


def test_clean_audit_report(capsys):
    """A fully trusted online inventory should have no alerts."""

    devices = [
        (
            "192.168.1.10",
            "AA:BB:CC:DD:EE:01",
            "Gaming-PC",
            "Example Vendor",
            None,
            None,
            "ONLINE",
            0,
        )
    ]

    results = audit.audit_devices(
        devices,
        {"AA:BB:CC:DD:EE:01"},
    )

    audit.print_audit_report(results)

    output = capsys.readouterr().out

    assert "No unrecognized online devices found." in output
    assert "Audit complete." in output


def test_main_success(
    monkeypatch, sample_devices, capsys
):
    """A successful audit should return exit code zero."""

    monkeypatch.setattr(
        audit,
        "load_trusted_macs",
        lambda: {"AA:BB:CC:DD:EE:01"},
    )

    monkeypatch.setattr(
        audit,
        "initialize_database",
        lambda: None,
    )

    monkeypatch.setattr(
        audit,
        "get_all_devices",
        lambda: sample_devices,
    )

    exit_code = audit.main()

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Audit complete." in output
    assert "Unrecognized online:" in output


def test_main_missing_trusted_config(
    monkeypatch, capsys
):
    """Missing trusted-device config should fail safely."""

    def missing_config():
        raise FileNotFoundError(
            "config/trusted_devices.json"
        )

    monkeypatch.setattr(
        audit,
        "load_trusted_macs",
        missing_config,
    )

    exit_code = audit.main()

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "[ERROR]" in output
    assert "Configure trusted devices" in output


def test_main_database_failure(
    monkeypatch, capsys
):
    """Database errors should return a nonzero exit code."""

    monkeypatch.setattr(
        audit,
        "load_trusted_macs",
        lambda: {"AA:BB:CC:DD:EE:01"},
    )

    def database_error():
        raise RuntimeError("Database unavailable")

    monkeypatch.setattr(
        audit,
        "initialize_database",
        database_error,
    )

    exit_code = audit.main()

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Could not read device inventory" in output
