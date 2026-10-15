
"""Tests for HomeOps-AI deployment readiness checks."""

import json

import pytest

from homeops.preflight import (
    REQUIRED_FILES,
    check_deployment,
    main,
)


@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary HomeOps-AI project."""

    for relative_path in REQUIRED_FILES:
        file_path = tmp_path / relative_path
        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        file_path.touch()

    return tmp_path


def create_trusted_config(project_dir, macs):
    """Create a temporary private trusted-device file."""

    config_path = (
        project_dir / "config" / "trusted_devices.json"
    )

    config_path.write_text(
        json.dumps({"trusted_macs": macs}),
        encoding="utf-8",
    )

    return config_path


def test_valid_deployment(project_dir):
    """A complete configuration should pass."""

    create_trusted_config(
        project_dir,
        ["AA:BB:CC:DD:EE:01"],
    )

    results = check_deployment(
        project_dir=project_dir,
        python_version=(3, 9),
    )

    assert all(
        status == "PASS"
        for status, _ in results
    )


def test_missing_required_file(project_dir):
    """Missing project files should fail preflight."""

    create_trusted_config(
        project_dir,
        ["AA:BB:CC:DD:EE:01"],
    )

    missing_file = project_dir / "homeops" / "scanner.py"
    missing_file.unlink()

    results = check_deployment(
        project_dir=project_dir,
        python_version=(3, 9),
    )

    assert (
        "FAIL",
        "Missing homeops/scanner.py",
    ) in results


def test_unsupported_python_version(project_dir):
    """Python versions below 3.9 should fail."""

    create_trusted_config(
        project_dir,
        ["AA:BB:CC:DD:EE:01"],
    )

    results = check_deployment(
        project_dir=project_dir,
        python_version=(3, 8),
    )

    assert any(
        status == "FAIL"
        and "Python 3.9" in message
        for status, message in results
    )


def test_missing_trusted_configuration(project_dir):
    """Missing private configuration should fail."""

    results = check_deployment(
        project_dir=project_dir,
        python_version=(3, 9),
    )

    assert (
        "FAIL",
        "Missing config/trusted_devices.json",
    ) in results


def test_empty_trusted_list(project_dir):
    """An empty trusted list should produce a warning."""

    create_trusted_config(
        project_dir,
        [],
    )

    results = check_deployment(
        project_dir=project_dir,
        python_version=(3, 9),
    )

    assert any(
        status == "WARN"
        and "empty" in message.lower()
        for status, message in results
    )

    assert not any(
        status == "FAIL"
        for status, _ in results
    )


def test_invalid_mac_configuration(project_dir):
    """Invalid MAC addresses should fail preflight."""

    create_trusted_config(
        project_dir,
        ["INVALID-MAC"],
    )

    results = check_deployment(
        project_dir=project_dir,
        python_version=(3, 9),
    )

    assert any(
        status == "FAIL"
        and "Invalid trusted-device configuration" in message
        for status, message in results
    )


def test_malformed_json_configuration(project_dir):
    """Malformed JSON should fail preflight."""

    config_path = (
        project_dir / "config" / "trusted_devices.json"
    )

    config_path.write_text(
        '{"trusted_macs": [',
        encoding="utf-8",
    )

    results = check_deployment(
        project_dir=project_dir,
        python_version=(3, 9),
    )

    assert any(
        status == "FAIL"
        and "Invalid trusted-device configuration" in message
        for status, message in results
    )


def test_preflight_main_success(monkeypatch, capsys):
    """Successful preflight should return exit code zero."""

    monkeypatch.setattr(
        "homeops.preflight.check_deployment",
        lambda: [
            ("PASS", "Python 3.9"),
            ("PASS", "Configuration valid"),
        ],
    )

    exit_code = main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Preflight passed" in output


def test_preflight_main_failure(monkeypatch, capsys):
    """Failed preflight should return a nonzero exit code."""

    monkeypatch.setattr(
        "homeops.preflight.check_deployment",
        lambda: [
            ("PASS", "Python 3.9"),
            ("FAIL", "Missing configuration"),
        ],
    )

    exit_code = main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Preflight failed" in output
