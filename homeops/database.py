"""Database utilities for HomeOps-AI."""

import sqlite3
from pathlib import Path
from datetime import datetime


DATABASE_PATH = Path("data/homeops.db")


def get_connection():
    """Create and return a SQLite database connection."""
    return sqlite3.connect(DATABASE_PATH)


def initialize_database():
    """Create the HomeOps-AI database tables if they do not exist."""
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
            status TEXT NOT NULL
        )
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

    Devices are primarily identified by MAC address.
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
                status = ?
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
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
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
    """Return a device record as a dictionary using its MAC address."""
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
            status
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
    }


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
            status
        FROM devices
        ORDER BY ip_address
        """
    )

    devices = cursor.fetchall()

    connection.close()

    return devices


if __name__ == "__main__":
    initialize_database()
    print("HomeOps-AI database initialized.")
