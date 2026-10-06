"""Main entry point for HomeOps-AI."""

from .database import initialize_database, save_device, get_all_devices
from .scanner import mock_scan


def main():
    """Run a HomeOps-AI network scan and update the device inventory."""

    print("HomeOps-AI")
    print("=" * 60)
    print("Starting network scan...\n")

    # Make sure the database exists.
    initialize_database()

    # Run the temporary mock scanner.
    scan_results = mock_scan()

    # Save every discovered device.
    for device in scan_results:
        save_device(device)

    # Retrieve the current inventory.
    devices = get_all_devices()

    print(f"{'IP ADDRESS':<18}{'HOSTNAME':<22}{'STATUS':<10}")
    print("-" * 50)

    for device in devices:
        ip_address = device[0]
        hostname = device[2] or "Unknown"
        status = device[6]

        print(
            f"{ip_address:<18}"
            f"{hostname:<22}"
            f"{status.upper():<10}"
        )

    print("-" * 50)

    online_count = sum(1 for device in devices if device[6] == "online")
    offline_count = sum(1 for device in devices if device[6] == "offline")

    print(f"Known devices: {len(devices)}")
    print(f"Online: {online_count}")
    print(f"Offline: {offline_count}")


if __name__ == "__main__":
    main()
