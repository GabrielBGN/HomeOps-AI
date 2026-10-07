"""Database utilities for HomeOps-AI."""

import sqlite3
from pathlib import Path
from datetime import datetime


DATABASE_PATH = Path("data/homeops.db")


def get_connection():
    """Create and return a SQLite database connection."""
    return sqlite3.connect(DATABASE_PATH)


def initialize_database():
    """Create and migrate the HomeOps-AI database."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            mac_address TEXT UNIQUE,
            hostname TEXT,
            vendor TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            status TEXT NOT NULL,
            missed_scans INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    # Upgrade older HomeOps-AI databases that do not yet
    # contain the missed_scans column.
    cursor.execute("PRAGMA table_info(devices)")
    columns = [column[1] for column in cursor.fetchall()]

    if "missed_scans" not in columns:
        cursor.execute(
            """
            ALTER TABLE devices
            ADD COLUMN missed_scans INTEGER NOT NULL DEFAULT 0
            """
        )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            status TEXT NOT NULL,
            latency_ms REAL,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
        """
    )

    connection.commit()
    connection.close()


def save_device(device):
    """
    Insert a new device or update an existing device.

    A successfully discovered device has its missed scan
    counter reset to zero.
    """
    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now().isoformat(timespec="seconds")

    cursor.execute(
        """
        SELECT id
        FROM devices
        WHERE mac_address = ?
        """,
        (device["mac_address"],),
    )

    existing_device = cursor.fetchone()

    if existing_device:
        cursor.execute(
            """
            UPDATE devices
            SET ip_address = ?,
                hostname = ?,
                vendor = ?,
                last_seen = ?,
                status = ?,
                missed_scans = 0
            WHERE mac_address = ?
            """,
            (
                device["ip_address"],
                device["hostname"],
                device["vendor"],
                device["last_seen"],
                device["status"],
                device["mac_address"],
            ),
        )
    else:
        cursor.execute(
            """
            INSERT INTO devices (
                ip_address,
                mac_address,
                hostname,
                vendor,
                first_seen,
                last_seen,
                status,
                missed_scans
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                device["ip_address"],
                device["mac_address"],
                device["hostname"],
                device["vendor"],
                now,
                device["last_seen"],
                device["status"],
            ),
        )

    connection.commit()
    connection.close()


def get_device_by_mac(mac_address):
    """Return a device record using its MAC address."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            ip_address,
            mac_address,
            hostname,
            vendor,
            first_seen,
            last_seen,
            status,
            missed_scans
        FROM devices
        WHERE mac_address = ?
        """,
        (mac_address,),
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return {
        "ip_address": row[0],
        "mac_address": row[1],
        "hostname": row[2],
        "vendor": row[3],
        "first_seen": row[4],
        "last_seen": row[5],
        "status": row[6],
        "missed_scans": row[7],
    }


def increment_missed_scan(mac_address):
    """Increment and return the missed scan count for a device."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE devices
        SET missed_scans = missed_scans + 1
        WHERE mac_address = ?
        """,
        (mac_address,),
    )

    cursor.execute(
        """
        SELECT missed_scans
        FROM devices
        WHERE mac_address = ?
        """,
        (mac_address,),
    )

    row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        return 0

    return row[0]


def mark_device_offline(mac_address):
    """Mark a known device as offline."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE devices
        SET status = 'offline'
        WHERE mac_address = ?
        """,
        (mac_address,),
    )

    connection.commit()
    connection.close()


def record_scan_history(device):
    """Store a historical snapshot of a device scan."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM devices
        WHERE mac_address = ?
        """,
        (device["mac_address"],),
    )

    row = cursor.fetchone()

    if row is None:
        connection.close()
        return

    device_id = row[0]

    cursor.execute(
        """
        INSERT INTO scan_history (
            device_id,
            timestamp,
            ip_address,
            status,
            latency_ms
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            device_id,
            datetime.now().isoformat(timespec="seconds"),
            device["ip_address"],
            device["status"],
            device.get("latency_ms"),
        ),
    )

    connection.commit()
    connection.close()


def get_all_devices():
    """Return all devices stored in the database."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            ip_address,
            mac_address,
            hostname,
            vendor,
            first_seen,
            last_seen,
            status,
            missed_scans
        FROM devices
        ORDER BY ip_address
        """
    )

    devices = cursor.fetchall()

    connection.close()

    return devices


def get_recent_scan_history(limit=20):
    """Return the most recent network scan history entries."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            devices.hostname,
            devices.mac_address,
            scan_history.ip_address,
            scan_history.status,
            scan_history.latency_ms,
            scan_history.timestamp
        FROM scan_history
        JOIN devices
            ON scan_history.device_id = devices.id
        ORDER BY scan_history.timestamp DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    connection.close()

    history = []

    for row in rows:
        history.append(
            {
                "hostname": row[0],
                "mac_address": row[1],
                "ip_address": row[2],
                "status": row[3],
                "latency_ms": row[4],
                "timestamp": row[5],
            }
        )

    return history


if __name__ == "__main__":
    initialize_database()
    print("HomeOps-AI database initialized.")
