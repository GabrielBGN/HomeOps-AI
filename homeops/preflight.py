
"""Deployment readiness checks for HomeOps-AI."""

import sys
from pathlib import Path

from .trusted_devices import load_trusted_macs


PROJECT_DIR = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "homeops/__main__.py",
    "homeops/scanner.py",
    "homeops/database.py",
    "homeops/security.py",
    "homeops/trusted_devices.py",
    "config/trusted_devices.example.json",
    "config/homeops-dashboard.service",
    "scripts/install_dashboard.sh",
]


def check_deployment(project_dir=None, python_version=None):
    """
    Check whether HomeOps-AI is ready for deployment.

    Returns a list of (status, message) tuples.
    """

    project_dir = (
        Path(project_dir)
        if project_dir is not None
        else PROJECT_DIR
    )

    python_version = (
        python_version
        if python_version is not None
        else sys.version_info[:2]
    )

    results = []

    # Check Python compatibility.
    if tuple(python_version) >= (3, 9):
        results.append((
            "PASS",
            f"Python {python_version[0]}.{python_version[1]}"
        ))
    else:
        results.append((
            "FAIL",
            "Python 3.9 or newer is required."
        ))

    # Check required project files.
    for relative_path in REQUIRED_FILES:
        file_path = project_dir / relative_path

        if file_path.is_file():
            results.append((
                "PASS",
                f"Found {relative_path}"
            ))
        else:
            results.append((
                "FAIL",
                f"Missing {relative_path}"
            ))

    # Check private trusted-device configuration.
    config_path = (
        project_dir / "config" / "trusted_devices.json"
    )

    if not config_path.is_file():
        results.append((
            "FAIL",
            "Missing config/trusted_devices.json"
        ))

    else:
        try:
            trusted_macs = load_trusted_macs(config_path)

        except (OSError, ValueError) as error:
            results.append((
                "FAIL",
                f"Invalid trusted-device configuration: {error}"
            ))

        else:
            if not trusted_macs:
                results.append((
                    "WARN",
                    "Trusted-device list is empty. "
                    "All discovered online devices with "
                    "valid MAC addresses will be flagged."
                ))
            else:
                results.append((
                    "PASS",
                    "Trusted-device configuration is valid "
                    f"({len(trusted_macs)} devices)"
                ))

    return results


def main():
    """Run deployment checks and print the results."""

    print("\nHomeOps-AI Deployment Preflight")
    print("=" * 60)

    results = check_deployment()

    for status, message in results:
        print(f"[{status}] {message}")

    print("-" * 60)

    failures = sum(
        1 for status, _ in results
        if status == "FAIL"
    )

    warnings = sum(
        1 for status, _ in results
        if status == "WARN"
    )

    if failures:
        print(
            f"Preflight failed: {failures} issue(s), "
            f"{warnings} warning(s)."
        )
        return 1

    print(
        f"Preflight passed with {warnings} warning(s)."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
