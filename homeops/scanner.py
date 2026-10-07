"""Network scanning utilities for HomeOps-AI."""

import ipaddress
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime


NETWORK = "192.168.1.0/24"


def ping_host(ip_address):
    """Ping a host and return its latency if reachable."""

    try:
        result = subprocess.run(
            [
                "ping",
                "-c",
                "1",
                "-W",
                "1",
                str(ip_address),
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )

        if result.returncode != 0:
            return None

        match = re.search(r"time[=<]([\d.]+)\s*ms", result.stdout)

        if match:
            return float(match.group(1))

        return 0.0

    except (subprocess.TimeoutExpired, ValueError):
        return None


def get_hostname(ip_address):
    """Attempt to resolve a hostname for an IP address."""

    try:
        hostname, _, _ = socket.gethostbyaddr(str(ip_address))
        return hostname
    except (socket.herror, socket.gaierror):
        return "Unknown"


def get_mac_address(ip_address):
    """Retrieve a MAC address from the Linux neighbor table."""

    try:
        result = subprocess.run(
            ["ip", "neigh", "show", str(ip_address)],
            capture_output=True,
            text=True,
        )

        match = re.search(
            r"lladdr\s+([0-9a-fA-F:]{17})",
            result.stdout,
        )

        if match:
            return match.group(1).lower()

    except OSError:
        pass

    return None


def scan_host(ip_address):
    """Scan a single host and return device information."""

    latency = ping_host(ip_address)

    if latency is None:
        return None

    timestamp = datetime.now().isoformat(timespec="seconds")

    return {
        "ip_address": str(ip_address),
        "mac_address": get_mac_address(ip_address),
        "hostname": get_hostname(ip_address),
        "vendor": "Unknown",
        "status": "online",
        "latency_ms": latency,
        "last_seen": timestamp,
    }


def scan_network():
    """Discover reachable devices on the local network."""

    network = ipaddress.ip_network(NETWORK)

    print(f"Scanning {network}...")

    devices = []

    with ThreadPoolExecutor(max_workers=32) as executor:
        results = executor.map(scan_host, network.hosts())

        for device in results:
            if device is not None and device["mac_address"] is not None:
                devices.append(device)

    return devices


if __name__ == "__main__":
    results = scan_network()

    print()
    print(f"{'IP ADDRESS':<18}{'HOSTNAME':<30}{'LATENCY':<12}")
    print("-" * 60)

    for device in results:
        print(
            f"{device['ip_address']:<18}"
            f"{device['hostname']:<30}"
            f"{device['latency_ms']} ms"
        )

    print()
    print(f"Devices discovered: {len(results)}")
