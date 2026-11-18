# HomeOps-AI

[![HomeOps-AI Tests](https://github.com/GabrielBGN/HomeOps-AI/actions/workflows/tests.yml/badge.svg)](https://github.com/GabrielBGN/HomeOps-AI/actions/workflows/tests.yml)

**HomeOps-AI** is a Python-based home-network monitoring and security project designed for a Raspberry Pi 4. It combines network discovery, persistent device tracking, automated scanning, security alerts, and historical availability analytics in a lightweight web dashboard. The long-term goal is to add AI-assisted network analysis and troubleshooting.

**Latest release:** `v1.2.0` — Network Analytics  
**Repository:** https://github.com/GabrielBGN/HomeOps-AI

## Features

- **Network inventory:** Track discovered devices using IP address, MAC address, hostname, vendor, first/last seen timestamps, and connectivity status.
- **Change detection:** Identify newly discovered devices, IP address changes, and online/offline transitions.
- **Security monitoring:** Flag unrecognized devices and display alerts for new, offline, and returning devices.
- **Offline threshold:** Mark a previously online device offline after three consecutive missed scans, reducing false alerts from transient failures.
- **Historical telemetry:** Store scan history and latency observations in SQLite.
- **Network analytics (v1.2.0):** Record `SEEN`/`MISSED` observations and calculate per-device availability from recorded scans.
- **Web dashboard:** View device inventory, alerts, scan history, and availability metrics in a browser.
- **Automated scanning:** A Linux `systemd` service and timer run the Python scanner every five minutes on the Raspberry Pi deployment.
- **Automated testing:** `pytest` test suite and GitHub Actions continuous integration; 82 tests passed at the v1.2.0 release.

> **Availability metric:** The displayed percentage represents the proportion of recorded scans in which a device was observed (`SEEN` / total observations × 100). It is **not** a continuous uptime or SLA measurement.

## Architecture

```text
              Home network
                   |
                   v
          Python network scanner <--- systemd timer (every 5 min)
                   |
                   v
         Device/change detection
                   |
          +--------+---------+
          |                  |
          v                  v
    Device inventory     Alerts / events
          |                  |
          +--------+---------+
                   |
                   v
      SQLite scan history + observations
                   |
                   v
        Python web dashboard (:8080)
                   |
                   v
       Future AI analysis / assistant
```

**Technology stack:** Python, Raspberry Pi 4, Linux, `systemd`, SQLite, TCP/IP networking, `pytest`, Git, and GitHub Actions.

## Getting started

Clone the repository and create a Python virtual environment:

```bash
git clone https://github.com/GabrielBGN/HomeOps-AI.git
cd HomeOps-AI
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run a scan manually:

```bash
python -m homeops
```

Run the automated tests:

```bash
python -m pytest -q
```

The web dashboard runs on port **8080** in the Raspberry Pi setup. See the repository's dashboard entry point and deployment configuration for the appropriate startup command. Run network discovery only on networks you own or are authorized to monitor.

### Raspberry Pi automation

The deployed monitoring workflow uses **two systemd units**:

1. A **service** starts the Python scanner.
2. A **timer** triggers the service every five minutes, without requiring an open terminal.

To inspect configured timers on the Pi:

```bash
systemctl list-timers --all
```

The timer handles scheduling; Python performs the actual scan. Bash or shell commands are used for installation and administration, not as the primary scheduling mechanism.

> **Deployment status:** v1.2.0 was merged, tagged, and tested in CI. Deployment and live verification of this version on the Raspberry Pi are still pending.

## Data and detection logic

SQLite persists device state, alerts, scan history, and per-scan observations. Devices are primarily tracked by MAC address, so an IP address change does not necessarily create a new device identity.

A missing response is recorded as `MISSED`; after **three consecutive missed scans**, a previously online device is marked offline. Successful detection records `SEEN` and supports recovery tracking. The analytics dashboard calculates scan-based availability from these observations.

## Releases

| Version | Highlights |
| --- | --- |
| **v1.0.0** | Device discovery, persistent SQLite inventory, scan history, initial web dashboard, scheduled scans |
| **v1.1.0** | New-device and connectivity alerts, unread alert counts, mark-as-read workflow |
| **v1.2.0** | `SEEN`/`MISSED` scan observations, device availability calculations, Network Analytics dashboard |

See [GitHub Releases](https://github.com/GabrielBGN/HomeOps-AI/releases) for published versions.

## Testing and CI

The project uses `pytest` for unit and workflow tests. Coverage includes device changes, scanning behavior, offline thresholds, alerts, database operations, availability calculations, and dashboard rendering.

At the v1.2.0 release, **82 automated tests passed locally and in GitHub Actions**. CI validates code behavior in a clean environment; it does not replace a live Raspberry Pi network test.

## Roadmap

- **Next deployment milestone:** Install and verify v1.2.0 on the Raspberry Pi, including live discovery, database writes, timer execution, and dashboard access.
- **AI-assisted network intelligence (planned):** Analyze historical observations for unusual connectivity or latency patterns, summarize incidents, and assist with troubleshooting.
- **Future infrastructure integrations (exploratory):** Additional observability, automation, and security tooling.

**AI status:** The monitoring data pipeline and analytics provide a foundation for AI features. AI/LLM-based anomaly detection and troubleshooting are **not yet confirmed as implemented** in v1.2.0.

## Security and privacy

- Monitor only networks you are authorized to scan.
- Keep credentials, API keys, private configuration, and local SQLite databases out of version control.
- Avoid exposing the dashboard directly to the public internet without authentication and appropriate network controls.
- Review configuration examples before running scans on your own subnet.

## Project purpose

HomeOps-AI is a practical homelab project for developing skills in **network engineering, Linux administration, Python backend development, security monitoring, automation, databases, and observability**—with a path toward AI-assisted operations.
