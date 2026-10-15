
"""Tests for HomeOps-AI interactive trusted-device setup."""

import json
import stat

import pytest

from homeops import trust_setup


@pytest.fixture
def setup_environment(tmp_path, monkeypatch):
    """Create a temporary environment for interactive setup."""

    config_path = (
        tmp_path / "config" / "trusted_devices.json"
    )

    monkeypatch.setattr(
        trust_setup,
        "TRUSTED_DEVICES_FILE",
        config_path,
    )

    devices = [
        {
            "ip_address": "192.168.1.10",
            "mac_address": "AA:BB:CC:DD:EE:01",
            "hostname": "Gaming-PC",
            "vendor": "Example Vendor",
            "status": "ONLINE",
        },
        {
            "ip_address": "192.168.1.20",
            "mac_address": "AA:BB:CC:DD:EE:02",
            "hostname": "Unknown-Phone",
            "vendor": "Example Vendor",
            "status": "ONLINE",
        },
    ]

    monkeypatch.setattr(
        trust_setup,
        "get_candidate_devices",
        lambda: devices,
    )

    return config_path, devices


def mock_answers(monkeypatch, answers):
    """Simulate answers to interactive prompts."""

    responses = iter(answers)

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(responses),
    )


def test_candidate_devices_from_database(monkeypatch):
    """Valid unique MAC addresses should become candidates."""

    database_initialized = []

    monkeypatch.setattr(
        trust_setup,
        "initialize_database",
        lambda: database_initialized.append(True),
    )

    database_devices = [
        (
            "192.168.1.10",
            "aa-bb-cc-dd-ee-01",
            "Gaming-PC",
            "Example",
            None,
            None,
            "ONLINE",
            0,
        ),
        (
            "192.168.1.11",
            "AA:BB:CC:DD:EE:01",
            "Duplicate-PC",
            "Example",
            None,
            None,
            "ONLINE",
            0,
        ),
        (
            "192.168.1.20",
            "INVALID-MAC",
            "Invalid",
            "Example",
            None,
            None,
            "ONLINE",
            0,
        ),
        (
            "192.168.1.30",
            "AA:BB:CC:DD:EE:03",
            None,
            None,
            None,
            None,
            "OFFLINE",
            3,
        ),
    ]

    monkeypatch.setattr(
        trust_setup,
        "get_all_devices",
        lambda: database_devices,
    )

    candidates = trust_setup.get_candidate_devices()

    assert database_initialized == [True]
    assert len(candidates) == 2

    assert candidates[0]["mac_address"] == (
        "AA:BB:CC:DD:EE:01"
    )

    assert candidates[1]["hostname"] == "Unknown"
    assert candidates[1]["vendor"] == "Unknown"


def test_approved_device_saved(
    setup_environment, monkeypatch
):
    """Only approved devices should be saved."""

    config_path, devices = setup_environment

    mock_answers(
        monkeypatch,
        ["y", "n", "YES"],
    )

    result = trust_setup.main()

    assert result == 0
    assert config_path.exists()

    config = json.loads(
        config_path.read_text(encoding="utf-8")
    )

    assert config["trusted_macs"] == [
        "AA:BB:CC:DD:EE:01"
    ]


def test_private_file_permissions(
    setup_environment, monkeypatch
):
    """Trusted-device configuration should be owner-only."""

    config_path, devices = setup_environment

    mock_answers(
        monkeypatch,
        ["yes", "no", "YES"],
    )

    result = trust_setup.main()

    assert result == 0

    permissions = stat.S_IMODE(
        config_path.stat().st_mode
    )

    assert permissions == 0o600


def test_existing_config_not_overwritten(
    setup_environment, monkeypatch
):
    """An existing configuration must remain unchanged."""

    config_path, devices = setup_environment

    config_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    original_content = json.dumps({
        "trusted_macs": ["AA:BB:CC:DD:EE:99"]
    })

    config_path.write_text(
        original_content,
        encoding="utf-8",
    )

    result = trust_setup.main()

    assert result == 1
    assert config_path.read_text(
        encoding="utf-8"
    ) == original_content


def test_no_devices_found(
    setup_environment, monkeypatch
):
    """Setup should stop when the database has no devices."""

    config_path, devices = setup_environment

    monkeypatch.setattr(
        trust_setup,
        "get_candidate_devices",
        lambda: [],
    )

    result = trust_setup.main()

    assert result == 1
    assert not config_path.exists()


def test_no_devices_approved(
    setup_environment, monkeypatch
):
    """Rejecting every device must not create a file."""

    config_path, devices = setup_environment

    mock_answers(
        monkeypatch,
        ["n", "n"],
    )

    result = trust_setup.main()

    assert result == 1
    assert not config_path.exists()


def test_user_cancels_setup(
    setup_environment, monkeypatch
):
    """Canceling confirmation must not save the list."""

    config_path, devices = setup_environment

    mock_answers(
        monkeypatch,
        ["y", "n", "NO"],
    )

    result = trust_setup.main()

    assert result == 1
    assert not config_path.exists()


def test_case_insensitive_approval(
    setup_environment, monkeypatch
):
    """Device approval should accept mixed-case answers."""

    config_path, devices = setup_environment

    mock_answers(
        monkeypatch,
        [" YeS ", " NO ", "YES"],
    )

    result = trust_setup.main()

    assert result == 0

    config = json.loads(
        config_path.read_text(encoding="utf-8")
    )

    assert len(config["trusted_macs"]) == 1
    assert config["trusted_macs"][0] == (
        "AA:BB:CC:DD:EE:01"
    )
