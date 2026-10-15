
import json
from pathlib import Path

from .security import (
    normalize_mac,
    find_unrecognized_devices,
)


# Locate the project directory automatically
PROJECT_DIR = Path(__file__).resolve().parent.parent

TRUSTED_DEVICES_FILE = (
    PROJECT_DIR / "config" / "trusted_devices.json"
)


def load_trusted_macs(config_path=None):
    """
    Load trusted MAC addresses from a JSON file.

    Returns a set of normalized MAC addresses.
    """

    path = (
        Path(config_path)
        if config_path is not None
        else TRUSTED_DEVICES_FILE
    )

    if not path.is_file():
        raise FileNotFoundError(
            f"Trusted device configuration not found: {path}. "
            "Create config/trusted_devices.json locally."
        )

    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    if (
        not isinstance(config, dict)
        or not isinstance(config.get("trusted_macs"), list)
    ):
        raise ValueError(
            "Configuration must contain a trusted_macs list."
        )

    trusted = set()

    for index, raw_mac in enumerate(config["trusted_macs"]):
        mac = normalize_mac(raw_mac)

        if mac is None:
            raise ValueError(
                f"Invalid MAC address at index {index}."
            )

        trusted.add(mac)

    return trusted


def check_unrecognized_devices(devices, config_path=None):
    """
    Compare scanned devices against the trusted list.

    Returns unrecognized online devices.
    """

    trusted_macs = load_trusted_macs(config_path)

    return find_unrecognized_devices(
        devices,
        trusted_macs
    )
