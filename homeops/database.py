"""Database utilities for HomeOps-AI."""

import sqlite3
from pathlib import Path


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
            mac_address TEXT,
            hostname TEXT,
            vendor TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            status TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()
    print("HomeOps-AI database initialized.")
