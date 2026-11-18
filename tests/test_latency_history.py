"""Tests for HomeOps-AI v1.3.0 SQLite latency-history retrieval."""

import sqlite3

import pytest

from homeops import database


@pytest.fixture
def latency_db(tmp_path, monkeypatch):
    """Initialize an isolated SQLite database, never the user's live database."""
    db_path = tmp_path / "homeops.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)
    database.initialize_database()
    connection = sqlite3.connect(db_path)
    try:
        connection.executemany(
            """INSERT INTO devices
               (ip_address, mac_address, hostname, first_seen, last_seen, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                ("192.168.1.10", "AA:AA:AA:AA:AA:AA", "device-a", "2026-01-01", "2026-01-01", "online"),
                ("192.168.1.11", "BB:BB:BB:BB:BB:BB", "device-b", "2026-01-01", "2026-01-01", "online"),
            ],
        )
        connection.commit()
    finally:
        connection.close()
    return db_path


def add_observation(db_path, mac, latency, status="SEEN", timestamp="2026-01-01T12:00:00"):
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.execute(
            """INSERT INTO scan_observations
               (device_id, timestamp, observed_status, confirmed_status, latency_ms)
               VALUES ((SELECT id FROM devices WHERE mac_address = ?), ?, ?, 'ONLINE', ?)""",
            (mac, timestamp, status, latency),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def test_returns_only_requested_device(latency_db):
    add_observation(latency_db, "AA:AA:AA:AA:AA:AA", 10.0)
    add_observation(latency_db, "BB:BB:BB:BB:BB:BB", 999.0)
    add_observation(latency_db, "AA:AA:AA:AA:AA:AA", 20.0)
    assert database.get_device_latency_history("AA:AA:AA:AA:AA:AA") == [10.0, 20.0]


def test_ignores_missing_negative_and_missed_measurements(latency_db):
    mac = "AA:AA:AA:AA:AA:AA"
    add_observation(latency_db, mac, 12.0)
    add_observation(latency_db, mac, None)
    add_observation(latency_db, mac, -5.0)
    add_observation(latency_db, mac, 500.0, status="MISSED")
    add_observation(latency_db, mac, 18.0)
    assert database.get_device_latency_history(mac) == [12.0, 18.0]


def test_limits_to_most_recent_and_returns_oldest_first(latency_db):
    mac = "AA:AA:AA:AA:AA:AA"
    for latency in [10.0, 20.0, 30.0, 40.0]:
        add_observation(latency_db, mac, latency)
    assert database.get_device_latency_history(mac, limit=2) == [30.0, 40.0]


def test_excludes_specified_observation_id(latency_db):
    mac = "AA:AA:AA:AA:AA:AA"
    add_observation(latency_db, mac, 10.0)
    current_id = add_observation(latency_db, mac, 100.0)
    assert database.get_device_latency_history(mac, exclude_observation_id=current_id) == [10.0]


def test_unknown_device_returns_empty_history(latency_db):
    assert database.get_device_latency_history("CC:CC:CC:CC:CC:CC") == []


@pytest.mark.parametrize("limit", [0, -1, 1.5, True, "5", None])
def test_invalid_limits_raise_value_error(latency_db, limit):
    with pytest.raises(ValueError):
        database.get_device_latency_history("AA:AA:AA:AA:AA:AA", limit=limit)
