# HomeOps-AI

[![HomeOps-AI Tests](https://github.com/GabrielBGN/HomeOps-AI/actions/workflows/tests.yml/badge.svg)](https://github.com/GabrielBGN/HomeOps-AI/actions/workflows/tests.yml)

**HomeOps-AI** is a Python-based network monitoring and AI-assisted troubleshooting platform built for a Raspberry Pi 4.

It combines automated network discovery, persistent device tracking, connectivity monitoring, latency analytics, security alerts, and an on-demand **AI Network Analyst** into a lightweight web dashboard.

**Latest release:** `v1.4.0` — AI Network Analyst  
**Platform:** Raspberry Pi 4 / Linux  
**Deployment status:** Successfully deployed and verified on Raspberry Pi  
**Repository:** https://github.com/GabrielBGN/HomeOps-AI

## Features

### Network Monitoring
- Discover devices connected to a local network.
- Maintain a persistent SQLite inventory of discovered devices.
- Track IP addresses, MAC addresses, hostnames, vendors, and connectivity status.
- Detect newly discovered devices and IP address changes.
- Identify devices transitioning between online and offline states.
- Apply a three-consecutive-missed-scans threshold before marking previously online devices offline.

### Network Analytics
- Record historical scan observations and device latency.
- Calculate per-device availability using `SEEN` and `MISSED` observations.
- Detect elevated latency and subsequent recovery.
- Display network history and performance information in a web dashboard.

**Note:** Device availability represents the percentage of recorded scans in which a device was observed. It does not measure continuous uptime.

### AI Network Analyst — v1.4.0

HomeOps-AI integrates with the OpenAI API to generate on-demand network health assessments.

The AI Network Analyst provides:

- Network health classification and severity assessment.
- Executive summaries of network conditions.
- Analysis of device availability and latency patterns.
- Identification of potential connectivity issues.
- Actionable troubleshooting recommendations.
- Explanations of data limitations and diagnostic uncertainty.

**Privacy-conscious design:**
- Network identifiers are sanitized before AI analysis.
- Raw IP addresses, MAC addresses, and hostnames are not intentionally included in AI requests.
- OpenAI API credentials remain in local environment configuration.
- AI analysis is initiated manually rather than automatically during every scan.
- API requests use `store=False`.

Each generated analysis makes a billable OpenAI API request.

### Web Dashboard

The dashboard provides a browser-based interface for:

- Total, online, and offline device counts.
- Unread network alerts.
- Device inventory and connectivity status.
- Historical device availability.
- Recent scan results and latency measurements.
- AI-generated network health assessments.

The dashboard automatically refreshes monitoring information.

### Automation and Reliability

- Linux `systemd` service and timer for scheduled network scanning.
- Approximately five-minute scan intervals.
- Separate `systemd` service for the dashboard.
- Persistent SQLite storage across restarts.
- Python virtual environment for dependency isolation.
- Automated testing with `pytest` and GitHub Actions.

## Architecture

```text
                  Home Network
                       |
                       v
               Network Discovery
                       |
                       v
              Python Scanner
                       ^
                       |
                systemd Timer
                 (~5 minutes)
                       |
                       v
              Device Monitoring
                 /         \
                v           v
          Connectivity    Latency
            Tracking      Analysis
                \           /
                 v         v
                 SQLite Database
                        |
                        v
                Web Dashboard
                 127.0.0.1:8080
                        |
                  Manual Request
                        |
                        v
                AI Network Analyst
                        |
                 Sanitized Summary
                        |
                        v
                    OpenAI API
                        |
                        v
               Network Health Report
```

## Technology Stack

| Component | Technology |
|---|---|
| Hardware | Raspberry Pi 4 |
| Programming language | Python |
| Operating system | Linux |
| Network monitoring | Python-based network discovery |
| Database | SQLite |
| Service management | systemd |
| AI integration | OpenAI API |
| Dashboard | Python HTTP server |
| Testing | pytest |
| CI/CD | GitHub Actions |
| Version control | Git and GitHub |
| Remote administration | SSH |

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/GabrielBGN/HomeOps-AI.git
cd HomeOps-AI
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure OpenAI (Optional)

Create a `.env` file in the project directory:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

Restrict file permissions:

```bash
chmod 600 .env
```

The network scanner and dashboard monitoring features can operate without an OpenAI API key. A key is required to generate AI network analyses.

**Never commit `.env` or expose API credentials in screenshots, logs, or public repositories.**

### 5. Run the Network Scanner

```bash
python -m homeops
```

### 6. Start the Dashboard

```bash
python -m homeops.dashboard
```

By default, the dashboard listens on:

```text
http://127.0.0.1:8080/
```

### 7. Run Automated Tests

```bash
python -m pytest -q
```

## Raspberry Pi Deployment

HomeOps-AI is deployed on a Raspberry Pi with two systemd services:

- `homeops.service` — Executes the network scanner.
- `homeops-dashboard.service` — Runs the web dashboard.

A separate `homeops.timer` schedules periodic scans.

### Check Service Status

```bash
systemctl status homeops-dashboard.service
systemctl status homeops.timer
```

### View Scheduled Scans

```bash
systemctl list-timers --all
```

### View Dashboard Logs

```bash
journalctl -u homeops-dashboard.service -n 30 --no-pager
```

### Access the Dashboard Remotely

The v1.4.0 dashboard binds to localhost to reduce network exposure.

From a remote computer, establish an SSH tunnel:

```bash
ssh -N -L 8080:127.0.0.1:8080 <pi-user>@<pi-host>
```

Then open:

```text
http://127.0.0.1:8080/
```

The local port must match the dashboard's configured allowed host and origin for AI analysis requests.

The Raspberry Pi continues monitoring independently when the SSH session is disconnected. The tunnel is only needed for remote dashboard access.

## Data and Detection Logic

HomeOps-AI uses SQLite to preserve monitoring information, including:

- Discovered device inventory.
- Device connectivity status.
- Network alerts.
- Scan history.
- Latency observations.
- Per-device availability observations.

Devices are primarily tracked by MAC address.

When a device does not respond to discovery, HomeOps-AI records a `MISSED` observation. After three consecutive missed scans, a previously online device is marked offline.

A successful observation records `SEEN` and supports reconnection detection.

Device availability is calculated as:

```text
Availability (%) = SEEN observations / Total observations × 100
```

A missed scan response does not necessarily indicate a physical network outage. Wireless power-saving behavior, device shutdowns, or discovery limitations can affect monitoring results.

## Release History

| Version | Highlights |
|---|---|
| **v1.0.0** | Network discovery, SQLite inventory, scan history, web dashboard, scheduled scans |
| **v1.1.0** | Connectivity alerts, unread alert counts, mark-as-read functionality |
| **v1.2.0** | Device availability tracking, `SEEN`/`MISSED` observations, historical network analytics |
| **v1.3.0** | Latency monitoring, high-latency detection, recovery alerts, and monitoring improvements |
| **v1.4.0** | AI Network Analyst, OpenAI integration, privacy-conscious network summaries, on-demand AI reports |

See [GitHub Releases](https://github.com/GabrielBGN/HomeOps-AI/releases) for release details.

## Testing and Continuous Integration

HomeOps-AI uses `pytest` to validate network monitoring behavior and application functionality.

Test coverage includes:

- Device discovery and change detection.
- Offline thresholds and reconnection handling.
- Database operations.
- Alert generation.
- Historical availability calculations.
- Latency monitoring.
- Dashboard behavior.
- AI analysis functionality and safeguards.

**v1.4.0 verification:** 167 automated tests passed, with GitHub Actions CI checks passing.

The application has also been tested on a Raspberry Pi using live network monitoring data and a successfully generated AI network health assessment.

## Security and Privacy

HomeOps-AI is designed for use on networks you own or have permission to monitor.

Security considerations include:

- Localhost-only dashboard access.
- Encrypted remote access using SSH tunneling.
- HTTP Host and Origin validation for protected AI requests.
- CSRF protection and request cooldowns.
- Local storage of OpenAI credentials.
- Sanitization of sensitive network identifiers before AI requests.
- No automatic AI requests during scheduled scans.
- Exclusion of credentials and local monitoring databases from version control.

**Important:** The dashboard is intended for trusted local access. Do not expose it directly to the public internet without additional authentication and security controls.

## Roadmap

Potential future improvements include:

- Better differentiation between inactive historical devices and recently disconnected devices.
- Improved device classification and identification.
- More advanced latency trend analysis.
- Additional network health visualizations.
- Improved AI troubleshooting context.
- Optional notifications for important network events.
- Expanded network observability integrations.

## Project Purpose

HomeOps-AI is a hands-on homelab project focused on building practical experience in:

- Network engineering and troubleshooting.
- Linux system administration.
- Python backend development.
- Network security monitoring.
- Database management.
- Infrastructure automation.
- API integration and AI-assisted operations.
- Testing, continuous integration, and production-style deployment.

The project demonstrates the development and deployment of a persistent network monitoring application on dedicated Raspberry Pi hardware, with AI-assisted analysis built on real network telemetry.

---

**HomeOps-AI v1.4.0 — AI Network Analyst**
