
"""Main entry point for HomeOps-AI."""

from .database import (
    initialize_database,
    save_device,
    get_all_devices,
    get_device_by_mac,
    record_scan_history,
    increment_missed_scan,
    mark_device_offline,
)

from .scanner import scan_network
from .change_detector import detect_changes
from .trusted_devices import check_unrecognized_devices


OFFLINE_THRESHOLD = 3


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
    """Run a network scan and update HomeOps-AI."""

    print("HomeOps-AI")
    print("=" * 60)
    print("Starting network scan...\n")

    # Initialize SQLite database.
    initialize_database()

    # Discover devices on the network.
    scan_results = scan_network()

    detected_changes = []
    seen_mac_addresses = set()

    # Process devices discovered during this scan.
    for device in scan_results:
        mac_address = device["mac_address"]

        if mac_address is None:
            continue

        seen_mac_addresses.add(mac_address)

        # Check whether the device was previously known.
        previous_device = get_device_by_mac(mac_address)

        # Detect new devices, IP changes, and status changes.
        changes = detect_changes(previous_device, device)
        detected_changes.extend(changes)

        # Save device information and scan history.
        # save_device() also resets missed_scans to zero.
        save_device(device)
        record_scan_history(device)

    # Check known devices that were not seen in this scan.
    known_devices = get_all_devices()

    for device in known_devices:
        ip_address = device[0]
        mac_address = device[1]
        hostname = device[2]
        vendor = device[3]
        first_seen = device[4]
        last_seen = device[5]
        status = device[6]

        if mac_address is None:
            continue

        # Skip devices found during the current scan.
        if mac_address in seen_mac_addresses:
            continue

        # Do not continue counting misses for offline devices.
        if status.upper() == "OFFLINE":
            continue

        missed_scans = increment_missed_scan(mac_address)

        print(
            f"[MISSED] {hostname or 'Unknown'} "
            f"({ip_address}) "
            f"{missed_scans}/{OFFLINE_THRESHOLD}"
        )

        # Wait for three consecutive missed scans.
        if missed_scans < OFFLINE_THRESHOLD:
            continue

        previous_device = {
            "ip_address": ip_address,
            "mac_address": mac_address,
            "hostname": hostname,
            "vendor": vendor,
            "first_seen": first_seen,
            "last_seen": last_seen,
            "status": status,
        }

        offline_device = {
            "ip_address": ip_address,
            "mac_address": mac_address,
            "hostname": hostname,
            "vendor": vendor,
            "status": "OFFLINE",
            "latency_ms": None,
            "last_seen": last_seen,
        }

        # Detect the transition from online to offline.
        changes = detect_changes(
            previous_device,
            offline_device,
        )

        detected_changes.extend(changes)

        # Update database and record the offline event.
        mark_device_offline(mac_address)
        record_scan_history(offline_device)

    # Display the updated network inventory.
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
        1 for device in devices
        if device[6].upper() == "ONLINE"
    )

    offline_count = sum(
        1 for device in devices
        if device[6].upper() == "OFFLINE"
    )

    print(f"Known devices: {len(devices)}")
    print(f"Online: {online_count}")
    print(f"Offline: {offline_count}")

    # Display detected network changes.
    print("\nNetwork Changes")
    print("-" * 60)

    if detected_changes:
        for change in detected_changes:
            print_change(change)
    else:
        print("No confirmed network changes detected.")

    # ---------------------------------------------
    # SECURITY MONITORING
    # ---------------------------------------------

    print("\nSecurity Review")
    print("-" * 60)

    try:
        # Compare scanned devices against trusted MACs.
        unrecognized = check_unrecognized_devices(
            scan_results
        )

    except (OSError, ValueError) as error:
        # Missing or invalid configuration should not
        # interrupt normal network monitoring.
        print(f"[SECURITY SKIPPED] {error}")

    else:
        if unrecognized:
            print(
                f"Unrecognized devices: {len(unrecognized)}"
            )

            for device in unrecognized:
                hostname = (
                    device.get("hostname") or "Unknown"
                )

                ip_address = (
                    device.get("ip_address") or "N/A"
                )

                mac_address = device["mac_address"]

                print(
                    f"[UNRECOGNIZED DEVICE] "
                    f"{hostname} "
                    f"({ip_address}) "
                    f"MAC: {mac_address}"
                )

        else:
            print(
                "No unrecognized online devices found."
            )

    print("\nScan complete.")


if __name__ == "__main__":
    main()
