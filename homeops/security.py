
import re


def normalize_mac(mac_address):
    """
    Convert MAC addresses into a consistent format.

    Example:
    aa-bb-cc-dd-ee-ff -> AA:BB:CC:DD:EE:FF
    """
    if not isinstance(mac_address, str):
        return None

    cleaned = re.sub(r"[:-]", "", mac_address.strip())

    if not re.fullmatch(r"[0-9a-fA-F]{12}", cleaned):
        return None

    cleaned = cleaned.upper()

    return ":".join(
        cleaned[i:i + 2]
        for i in range(0, 12, 2)
    )


def find_unrecognized_devices(devices, trusted_macs):
    """
    Identify online devices whose MAC addresses
    are not in the trusted device list.

    devices: List of device dictionaries from scanner.py
    trusted_macs: Collection of trusted MAC addresses

    Returns a list of unrecognized devices.
    """

    trusted = {
        normalized
        for mac in trusted_macs
        if (normalized := normalize_mac(mac)) is not None
    }

    unrecognized = []
    seen = set()

    for device in devices:
        if device.get("status", "").upper() != "ONLINE":
            continue

        mac = normalize_mac(device.get("mac_address"))

        if mac is None:
            continue

        if mac in trusted or mac in seen:
            continue

        seen.add(mac)

        unrecognized.append({
            "ip_address": device.get("ip_address"),
            "mac_address": mac,
            "hostname": device.get("hostname"),
            "vendor": device.get("vendor"),
            "status": "UNRECOGNIZED",
        })

    return unrecognized
