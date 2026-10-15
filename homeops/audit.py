
"""Network security audit for HomeOps-AI."""

from .database import initialize_database, get_all_devices
from .security import normalize_mac
from .trusted_devices import load_trusted_macs


def audit_devices(devices, trusted_macs):
    """
    Review known devices against the trusted MAC list.

    This function does not perform a network scan or
    modify the database.

    Returns a summary dictionary.
    """

    trusted = set()

    for mac_address in trusted_macs:
        normalized = normalize_mac(mac_address)

        if normalized is not None:
            trusted.add(normalized)

    results = {
        "total": 0,
        "online": 0,
        "offline": 0,
        "trusted_online": 0,
        "unrecognized_online": 0,
        "unverifiable_online": 0,
        "devices": [],
    }

    for device in devices:
        ip_address = device[0] or "Unknown"
        mac_address = normalize_mac(device[1])
        hostname = device[2] or "Unknown"
        vendor = device[3] or "Unknown"
        status = str(device[6] or "UNKNOWN").upper()

        if mac_address is None:
            trust_status = "UNVERIFIABLE"
        elif mac_address in trusted:
            trust_status = "TRUSTED"
        else:
            trust_status = "UNRECOGNIZED"

        record = {
            "ip_address": ip_address,
            "mac_address": mac_address,
            "hostname": hostname,
            "vendor": vendor,
            "status": status,
            "trust_status": trust_status,
        }

        results["devices"].append(record)
        results["total"] += 1

        if status == "ONLINE":
            results["online"] += 1

            if trust_status == "TRUSTED":
                results["trusted_online"] += 1

            elif trust_status == "UNRECOGNIZED":
                results["unrecognized_online"] += 1

            else:
                results["unverifiable_online"] += 1

        elif status == "OFFLINE":
            results["offline"] += 1

    return results


def print_audit_report(results):
    """Display a readable network security report."""

    print("\nHomeOps-AI Network Security Audit")
    print("=" * 60)

    print(f"Known devices:        {results['total']}")
    print(f"Online devices:       {results['online']}")
    print(f"Offline devices:      {results['offline']}")
    print(f"Trusted online:       {results['trusted_online']}")
    print(
        f"Unrecognized online:  "
        f"{results['unrecognized_online']}"
    )
    print(
        f"Unverifiable online:  "
        f"{results['unverifiable_online']}"
    )

    print("\nDevices Requiring Review")
    print("-" * 60)

    devices_to_review = [
        device
        for device in results["devices"]
        if device["status"] == "ONLINE"
        and device["trust_status"] != "TRUSTED"
    ]

    if not devices_to_review:
        print("No unrecognized online devices found.")

    else:
        for device in devices_to_review:
            print()
            print(
                f"[{device['trust_status']}] "
                f"{device['hostname']}"
            )
            print(f"  IP:     {device['ip_address']}")
            print(
                f"  MAC:    "
                f"{device['mac_address'] or 'Unknown'}"
            )
            print(f"  Vendor: {device['vendor']}")

    print("\n" + "=" * 60)
    print("Audit complete.")

    if devices_to_review:
        print(
            "Review these devices before deciding "
            "whether to trust them."
        )

    print(
        "This report uses the saved device inventory. "
        "It is not a live network scan."
    )


def main():
    """Run the security audit using local project data."""

    try:
        trusted_macs = load_trusted_macs()

    except (OSError, ValueError) as error:
        print(f"[ERROR] Trusted-device configuration: {error}")
        print(
            "Configure trusted devices before "
            "running the security audit."
        )
        return 1

    try:
        initialize_database()
        devices = get_all_devices()

    except Exception as error:
        print(f"[ERROR] Could not read device inventory: {error}")
        return 1

    results = audit_devices(devices, trusted_macs)
    print_audit_report(results)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
