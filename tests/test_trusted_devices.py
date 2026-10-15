
import json

import pytest

from homeops.trusted_devices import (
    load_trusted_macs,
    check_unrecognized_devices,
)


def create_config(tmp_path, trusted_macs):
    """Create a temporary trusted-device configuration."""

    config_file = tmp_path / "trusted_devices.json"

    config_file.write_text(
        json.dumps({"trusted_macs": trusted_macs}),
        encoding="utf-8",
    )

    return config_file


def test_load_trusted_macs(tmp_path):
    """Valid MAC addresses should load successfully."""

    config_file = create_config(
        tmp_path,
        [
            "aa-bb-cc-dd-ee-01",
            "AA:BB:CC:DD:EE:02",
        ],
    )

    result = load_trusted_macs(config_file)

    assert result == {
        "AA:BB:CC:DD:EE:01",
        "AA:BB:CC:DD:EE:02",
    }


def test_duplicate_trusted_macs(tmp_path):
    """Duplicate MAC addresses should be removed."""

    config_file = create_config(
        tmp_path,
        [
            "AA:BB:CC:DD:EE:01",
            "aa-bb-cc-dd-ee-01",
        ],
    )

    result = load_trusted_macs(config_file)

    assert len(result) == 1


def test_missing_configuration(tmp_path):
    """Missing configuration must raise an error."""

    missing_file = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        load_trusted_macs(missing_file)


def test_invalid_mac_address(tmp_path):
    """Invalid MAC addresses must be rejected."""

    config_file = create_config(
        tmp_path,
        ["invalid-mac"],
    )

    with pytest.raises(ValueError):
        load_trusted_macs(config_file)


def test_invalid_json_structure(tmp_path):
    """The configuration must contain a list."""

    config_file = tmp_path / "trusted_devices.json"

    config_file.write_text(
        '{"trusted_macs": "not-a-list"}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_trusted_macs(config_file)


def test_malformed_json(tmp_path):
    """Malformed JSON must raise a parsing error."""

    config_file = tmp_path / "trusted_devices.json"

    config_file.write_text(
        '{"trusted_macs": [',
        encoding="utf-8",
    )

    with pytest.raises(json.JSONDecodeError):
        load_trusted_macs(config_file)


def test_unrecognized_device_detection(tmp_path):
    """Only unknown online devices should be flagged."""

    config_file = create_config(
        tmp_path,
        ["AA:BB:CC:DD:EE:01"],
    )

    devices = [
        {
            "ip_address": "192.168.1.10",
            "mac_address": "AA:BB:CC:DD:EE:01",
            "hostname": "Trusted-PC",
            "vendor": "Example",
            "status": "ONLINE",
        },
        {
            "ip_address": "192.168.1.20",
            "mac_address": "AA:BB:CC:DD:EE:02",
            "hostname": "Unknown-Phone",
            "vendor": "Example",
            "status": "ONLINE",
        },
        {
            "ip_address": "192.168.1.30",
            "mac_address": "AA:BB:CC:DD:EE:03",
            "hostname": "Offline-Device",
            "vendor": "Example",
            "status": "OFFLINE",
        },
    ]

    result = check_unrecognized_devices(
        devices,
        config_file,
    )

    assert len(result) == 1
    assert result[0]["hostname"] == "Unknown-Phone"
    assert result[0]["status"] == "UNRECOGNIZED"
