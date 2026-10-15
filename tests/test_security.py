
from homeops.security import (
    normalize_mac,
    find_unrecognized_devices,
)


def make_device(mac, status="ONLINE"):
    """Create a sample device for testing."""
    return {
        "ip_address": "192.168.1.50",
        "mac_address": mac,
        "hostname": "Test-Device",
        "vendor": "Test Vendor",
        "status": status,
    }


def test_normalize_mac():
    """MAC addresses should use a consistent format."""

    result = normalize_mac("aa-bb-cc-dd-ee-ff")

    assert result == "AA:BB:CC:DD:EE:FF"


def test_invalid_mac():
    """Invalid MAC addresses should be rejected."""

    assert normalize_mac("invalid-mac") is None
    assert normalize_mac(None) is None


def test_trusted_device():
    """Trusted devices should not be flagged."""

    devices = [
        make_device("AA:BB:CC:DD:EE:FF")
    ]

    trusted = ["aa-bb-cc-dd-ee-ff"]

    result = find_unrecognized_devices(
        devices, trusted
    )

    assert result == []


def test_unrecognized_device():
    """Unknown online devices should be flagged."""

    devices = [
        make_device("AA:BB:CC:DD:EE:FF")
    ]

    trusted = []

    result = find_unrecognized_devices(
        devices, trusted
    )

    assert len(result) == 1
    assert result[0]["status"] == "UNRECOGNIZED"
    assert result[0]["mac_address"] == "AA:BB:CC:DD:EE:FF"


def test_offline_device():
    """Offline devices should not be flagged."""

    devices = [
        make_device(
            "AA:BB:CC:DD:EE:FF",
            status="OFFLINE"
        )
    ]

    result = find_unrecognized_devices(
        devices, []
    )

    assert result == []


def test_duplicate_device():
    """The same MAC address should only appear once."""

    devices = [
        make_device("AA:BB:CC:DD:EE:FF"),
        make_device("aa-bb-cc-dd-ee-ff"),
    ]

    result = find_unrecognized_devices(
        devices, []
    )

    assert len(result) == 1


def test_multiple_devices():
    """Only unrecognized online devices are returned."""

    devices = [
        make_device("AA:BB:CC:DD:EE:01"),
        make_device("AA:BB:CC:DD:EE:02"),
        make_device("AA:BB:CC:DD:EE:03", "OFFLINE"),
    ]

    trusted = ["AA:BB:CC:DD:EE:01"]

    result = find_unrecognized_devices(
        devices, trusted
    )

    assert len(result) == 1
    assert result[0]["mac_address"] == "AA:BB:CC:DD:EE:02"
