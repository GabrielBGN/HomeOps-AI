"""Tests for HomeOps-AI v1.2.0 scan observations."""

import sqlite3

import pytest

import homeops.database as database


@pytest.fixture
def observation_database(tmp_path, monkeypatch):
    """Create an isolated SQLite database for each test."""
    db_path = tmp_path / "homeops.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)

    database.initialize_database()

    connection = sqlite3.connect(db_path)
    connection.execute(
        """
        INSERT INTO devices (
            ip_address, mac_address, hostname, vendor,
            first_seen, last_seen, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "192.168.1.50",
            "AA:BB:CC:DD:EE:50",
            "Test-PC",
            "Example Vendor",
            "2026-10-01",
            "2026-10-15",
            "ONLINE",
        ),
    )
    connection.commit()
    connection.close()

    return db_path


def read_observations(db_path):
    """Read saved observations directly from SQLite."""
    with sqlite3.connect(db_path) as connection:
        return connection.execute(
            """
            SELECT
                devices.mac_address,
                observed_status,
                confirmed_status,
                latency_ms
            FROM scan_observations
            JOIN devices
                ON scan_observations.device_id = devices.id
            ORDER BY scan_observations.id
            """
        ).fetchall()


def test_seen_observation(observation_database):
    result = database.record_scan_observation(
        "AA:BB:CC:DD:EE:50",
        "SEEN",
        "ONLINE",
        12.5,
    )

    assert result is True
    assert read_observations(observation_database) == [
        ("AA:BB:CC:DD:EE:50", "SEEN", "ONLINE", 12.5)
    ]


def test_missed_observation(observation_database):
    result = database.record_scan_observation(
        "AA:BB:CC:DD:EE:50",
        "MISSED",
        "OFFLINE",
        99.0,
    )

    assert result is True
    assert read_observations(observation_database) == [
        ("AA:BB:CC:DD:EE:50", "MISSED", "OFFLINE", None)
    ]


def test_missing_but_not_yet_offline(observation_database):
    result = database.record_scan_observation(
        "AA:BB:CC:DD:EE:50",
        "MISSED",
        "ONLINE",
    )

    assert result is True
    assert read_observations(observation_database) == [
        ("AA:BB:CC:DD:EE:50", "MISSED", "ONLINE", None)
    ]


@pytest.mark.parametrize(
    "observed_status,confirmed_status",
    [
        ("UNKNOWN", "ONLINE"),
        ("SEEN", "UNKNOWN"),
    ],
)
def test_invalid_status_rejected(
    observation_database,
    observed_status,
    confirmed_status,
):
    with pytest.raises(ValueError):
        database.record_scan_observation(
            "AA:BB:CC:DD:EE:50",
            observed_status,
            confirmed_status,
        )

    assert read_observations(observation_database) == []


def test_unknown_device_not_recorded(observation_database):
    result = database.record_scan_observation(
        "AA:BB:CC:DD:EE:99",
        "SEEN",
        "ONLINE",
    )

    assert result is False
    assert read_observations(observation_database) == []


def test_existing_tables_unaffected(observation_database):
    database.record_scan_observation(
        "AA:BB:CC:DD:EE:50",
        "SEEN",
        "ONLINE",
    )

    with sqlite3.connect(observation_database) as connection:
        history_count = connection.execute(
            "SELECT COUNT(*) FROM scan_history"
        ).fetchone()[0]

        alerts_count = connection.execute(
            "SELECT COUNT(*) FROM alerts"
        ).fetchone()[0]

    assert history_count == 0
    assert alerts_count == 0