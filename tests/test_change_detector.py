"""Tests for HomeOps-AI network change detection."""

from homeops.change_detector import detect_changes


def test_new_device_detection():
    current_device = {
        "ip_address": "192.168.1.50",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "hostname": "test-device",
        "status": "online",
    }

    changes = detect_changes(None, current_device)

    assert len(changes) == 1
    assert changes[0]["type"] == "new_device"


def test_status_change_detection():
    previous_device = {
        "ip_address": "192.168.1.50",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "hostname": "test-device",
        "status": "online",
    }

    current_device = {
        "ip_address": "192.168.1.50",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "hostname": "test-device",
        "status": "offline",
    }

    changes = detect_changes(previous_device, current_device)

    assert len(changes) == 1
    assert changes[0]["type"] == "status_change"
    assert changes[0]["old_status"] == "online"
    assert changes[0]["new_status"] == "offline"


def test_ip_change_detection():
    previous_device = {
        "ip_address": "192.168.1.50",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "hostname": "test-device",
        "status": "online",
    }

    current_device = {
        "ip_address": "192.168.1.60",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "hostname": "test-device",
        "status": "online",
    }

    changes = detect_changes(previous_device, current_device)

    assert len(changes) == 1
    assert changes[0]["type"] == "ip_change"
    assert changes[0]["old_ip"] == "192.168.1.50"
    assert changes[0]["new_ip"] == "192.168.1.60"


def test_no_change_detection():
    previous_device = {
        "ip_address": "192.168.1.50",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "hostname": "test-device",
        "status": "online",
    }

    current_device = previous_device.copy()

    changes = detect_changes(previous_device, current_device)

    assert changes == []
