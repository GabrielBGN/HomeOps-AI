"""Network scanning utilities for HomeOps-AI."""

from datetime import datetime


def mock_scan():
    """
    Return simulated network scan results.

    This will be replaced with real network discovery
    when HomeOps-AI is deployed to the Raspberry Pi.
    """
    timestamp = datetime.now().isoformat(timespec="seconds")

    devices = [
        {
            "ip_address": "192.168.1.1",
            "mac_address": "00:11:22:33:44:01",
            "hostname": "gateway",
            "vendor": "Unknown",
            "status": "online",
            "last_seen": timestamp,
        },
        {
            "ip_address": "192.168.1.20",
            "mac_address": "00:11:22:33:44:02",
            "hostname": "desktop",
            "vendor": "Unknown",
            "status": "online",
            "last_seen": timestamp,
        },
        {
            "ip_address": "192.168.1.30",
            "mac_address": "00:11:22:33:44:03",
            "hostname": "ubuntu-server",
            "vendor": "Unknown",
            "status": "offline",
            "last_seen": timestamp,
        },
    ]

    return devices


if __name__ == "__main__":
    results = mock_scan()

    print("HomeOps-AI Mock Network Scan")
    print("-" * 50)

    for device in results:
        print(
            f"{device['ip_address']:<16}"
            f"{device['hostname']:<20}"
            f"{device['status'].upper()}"
        )
