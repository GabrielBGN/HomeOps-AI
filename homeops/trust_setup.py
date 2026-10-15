
"""Interactive trusted-device setup for HomeOps-AI."""

import json
import os

from .database import (
    initialize_database,
    get_all_devices,
)
from .security import normalize_mac
from .trusted_devices import TRUSTED_DEVICES_FILE


def get_candidate_devices():
    """
    Read discovered devices from SQLite.

    Return unique devices with valid MAC addresses.
    """

    initialize_database()
    database_devices = get_all_devices()

    candidates = []
    seen_macs = set()

    for device in database_devices:
        ip_address = device[0]
        mac_address = normalize_mac(device[1])
        hostname = device[2]
        vendor = device[3]
        status = device[6]

        if mac_address is None:
            continue

        if mac_address in seen_macs:
            continue

        seen_macs.add(mac_address)

        candidates.append({
            "ip_address": ip_address or "Unknown",
            "mac_address": mac_address,
            "hostname": hostname or "Unknown",
            "vendor": vendor or "Unknown",
            "status": status or "Unknown",
        })

    return candidates


def main():
    """Interactively create the private trusted-device list."""

    print("\nHomeOps-AI Trusted Device Setup")
    print("=" * 60)

    config_path = TRUSTED_DEVICES_FILE

    # Never overwrite an existing trusted-device configuration.
    if config_path.exists():
        print(
            "[STOP] Trusted-device configuration "
            "already exists."
        )
        print(f"File: {config_path}")
        print("Edit the existing file to make changes.")
        return 1

    devices = get_candidate_devices()

    if not devices:
        print("No devices found in the database.")
        print("Run a network scan before setup.")
        return 1

    print(f"Discovered devices: {len(devices)}")
    print()
    print(
        "Review each device carefully before trusting it."
    )
    print(
        "Only approve devices you recognize and own "
        "or explicitly authorize."
    )

    trusted_macs = set()

    for index, device in enumerate(devices, start=1):
        print("\n" + "-" * 60)
        print(f"Device {index}/{len(devices)}")
        print(f"Hostname: {device['hostname']}")
        print(f"IP:       {device['ip_address']}")
        print(f"MAC:      {device['mac_address']}")
        print(f"Vendor:   {device['vendor']}")
        print(f"Status:   {device['status']}")

        answer = input(
            "\nTrust this device? [y/N]: "
        ).strip().lower()

        if answer in ("y", "yes"):
            trusted_macs.add(device["mac_address"])
            print("[TRUSTED] Device selected.")
        else:
            print("[SKIPPED] Device not selected.")

    print("\n" + "=" * 60)
    print(f"Selected trusted devices: {len(trusted_macs)}")

    if not trusted_macs:
        print("No devices selected. Nothing was saved.")
        return 1

    confirmation = input(
        "Save the private trusted-device list? "
        "Type YES to confirm: "
    ).strip()

    if confirmation != "YES":
        print("Setup canceled. Nothing was saved.")
        return 1

    config_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    config_data = {
        "trusted_macs": sorted(trusted_macs)
    }

    try:
        # Create a new file with private permissions.
        # O_EXCL prevents overwriting an existing file.
        file_descriptor = os.open(
            config_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )

        with os.fdopen(
            file_descriptor,
            "w",
            encoding="utf-8",
        ) as config_file:
            json.dump(
                config_data,
                config_file,
                indent=2,
            )
            config_file.write("\n")

    except FileExistsError:
        print(
            "[ERROR] Configuration already exists. "
            "No changes were made."
        )
        return 1

    except OSError as error:
        print(f"[ERROR] Could not save configuration: {error}")
        return 1

    print("\n[SUCCESS] Trusted-device list created.")
    print(f"File: {config_path}")
    print(f"Trusted devices: {len(trusted_macs)}")
    print(
        "This file is local and excluded from Git."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
