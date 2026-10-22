"""Tests for HomeOps-AI v1.2.0 device availability analytics."""

import sqlite3

import pytest

import homeops.database as database


@pytest.fixture
def availability_database(tmp_path, monkeypatch):
    """Create an isolated database containing two devices."""
    db_path = tmp_path / "homeops.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)

    database.initialize_database()

    with sqlite3.connect(db_path) as connection:
        connection.executemany(
            """
            INSERT INTO devices (
                ip_address, mac_address, hostname, vendor,
                first_seen, last_seen, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "192.168.1.10", "AA:BB:CC:DD:EE:10",
                    "Laptop", "Example",
                    "2026-10-01", "2026-10-21", "ONLINE",
                ),
                (
                    "192.168.1.20", "AA:BB:CC:DD:EE:20",
                    "Desktop", "Example",
                    "2026-10-01", "2026-10-21", "OFFLINE",
                ),
            ],
        )

    return db_path


def add_observations(mac_address, seen, missed):
    """Add test observations using the public database function."""
    for _ in range(seen):
        database.record_scan_observation(
            mac_address, "SEEN", "ONLINE"
        )

    for _ in range(missed):
        database.record_scan_observation(
            mac_address, "MISSED", "OFFLINE"
        )


def get_device(mac_address):
    """Find a device in the availability results."""
    return next(
        device
        for device in database.get_device_availability()
        if device["mac_address"] == mac_address
    )


def test_100_percent_availability(availability_database):
    add_observations("AA:BB:CC:DD:EE:10", 5, 0)

    device = get_device("AA:BB:CC:DD:EE:10")

    assert device["availability_pct"] == 100.0
    assert device["total_observations"] == 5
    assert device["seen_count"] == 5
    assert device["missed_count"] == 0


def test_50_percent_availability(availability_database):
    add_observations("AA:BB:CC:DD:EE:10", 3, 3)

    device = get_device("AA:BB:CC:DD:EE:10")

    assert device["availability_pct"] == 50.0
    assert device["total_observations"] == 6


def test_zero_percent_availability(availability_database):
    add_observations("AA:BB:CC:DD:EE:10", 0, 4)

    device = get_device("AA:BB:CC:DD:EE:10")

    assert device["availability_pct"] == 0.0
    assert device["missed_count"] == 4


def test_no_observations(availability_database):
    device = get_device("AA:BB:CC:DD:EE:10")

    assert device["availability_pct"] is None
    assert device["total_observations"] == 0
    assert device["seen_count"] == 0
    assert device["missed_count"] == 0


def test_multiple_devices(availability_database):
    add_observations("AA:BB:CC:DD:EE:10", 3, 1)
    add_observations("AA:BB:CC:DD:EE:20", 1, 3)

    laptop = get_device("AA:BB:CC:DD:EE:10")
    desktop = get_device("AA:BB:CC:DD:EE:20")

    assert laptop["availability_pct"] == 75.0
    assert desktop["availability_pct"] == 25.0
    assert len(database.get_device_availability()) == 2


def test_fractional_availability_rounding(availability_database):
    add_observations("AA:BB:CC:DD:EE:10", 2, 1)

    device = get_device("AA:BB:CC:DD:EE:10")

    assert device["availability_pct"] == 66.67