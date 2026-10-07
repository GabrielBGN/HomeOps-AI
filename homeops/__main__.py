"""Main entry point for HomeOps-AI."""

from .database import (
    initialize_database,
    save_device,
    get_all_devices,
    get_device_by_mac,
    record_scan_history,
)
from .scanner import scan_network
from .change_detector import detect_changes


def print_change(change):
    """Display a detected network change."""

    if change["type"] == "new_device":
        print(
            f"[NEW DEVICE] "
            f"{change['hostname']} "
            f"({change['ip_address']})"
        )

    elif change["type"] == "status_change":
        print(
            f"[STATUS CHANGE] "
            f"{change['hostname']}: "
            f"{change['old_status'].upper()} -> "
            f"{change['new_status'].upper()}"
        )

    elif change["type"] == "ip_change":
        print(
            f"[IP CHANGE] "
            f"{change['hostname']}: "
            f"{change['old_ip']} -> "
            f"{change['new_ip']}"
        )


def main():
    """Run a HomeOps-AI network scan and update the device inventory."""

    print("HomeOps-AI")
    print("=" * 60)
    print("Starting network scan...\n")

    initialize_database()

    scan_results = scan_network()

    detected_changes = []

    for device in scan_results:
        previous_device = get_device_by_mac(device["mac_address"])

        changes = detect_changes(previous_device, device)
        detected_changes.extend(changes)

        save_device(device)
        record_scan_history(device)

    devices = get_all_devices()

    print()
    print(f"{'IP ADDRESS':<18}{'HOSTNAME':<30}{'STATUS':<10}")
    print("-" * 60)

    for device in devices:
        ip_address = device[0]
        hostname = device[2] or "Unknown"
        status = device[6]

        print(
            f"{ip_address:<18}"
            f"{hostname:<30}"
            f"{status.upper():<10}"
        )

    print("-" * 60)

    online_count = sum(
        1 for device in devices if device[6] == "online"
    )

    offline_count = sum(
        1 for device in devices if device[6] == "offline"
    )

    print(f"Known devices: {len(devices)}")
    print(f"Online: {online_count}")
    print(f"Offline: {offline_count}")

    print("\nNetwork Changes")
    print("-" * 60)

    if detected_changes:
        for change in detected_changes:
            print_change(change)
    else:
        print("No network changes detected.")


if __name__ == "__main__":
    main()
