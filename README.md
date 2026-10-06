# HomeOps-AI

HomeOps-AI is a Raspberry Pi-based home network operations platform designed to combine networking, cybersecurity, automation, monitoring, and AI-assisted troubleshooting into one practical homelab project.

The long-term goal is to create an always-on network operations and security assistant capable of discovering devices, monitoring network health, detecting infrastructure changes, storing historical telemetry, automating administrative tasks, and using AI to assist with troubleshooting and incident analysis.

## Current Status

HomeOps-AI is currently in **V1 - Network Monitor** development.

The application currently supports:

- Persistent device inventory using SQLite
- First-seen and last-seen device tracking
- Online/offline device status
- Network change detection
- New device detection
- IP address change detection
- Device status change detection
- Historical scan telemetry
- Latency data storage
- Mock network scans for development and testing
- Automated tests with pytest

The current scanner uses simulated network data while the application architecture is developed and tested.

The mock scanner will be replaced with real network discovery when HomeOps-AI is deployed to the Raspberry Pi.

---

## Architecture

```text
                     Home Network
                          |
                          v
                   Network Scanner
                          |
                          v
                   Device Discovery
                          |
                          v
                    Change Detector
                          |
              +-----------+-----------+
              |                       |
              v                       v
       Device Inventory          Scan History
           SQLite                   SQLite
              |                       |
              +-----------+-----------+
                          |
                          v
                     HomeOps CLI
                          |
                          v
                 Future AI Assistant
```

HomeOps-AI separates network discovery from monitoring and storage logic.

This allows the current mock scanner to eventually be replaced by a real Raspberry Pi network scanner without redesigning the rest of the application.

---

## Project Structure

```text
HomeOps-AI/
|
├── config/
│   └── config.example.yaml
|
├── data/
│   └── .gitkeep
|
├── diagrams/
│
├── docs/
│   ├── architecture.md
│   └── network-design.md
|
├── homeops/
│   ├── __init__.py
│   ├── __main__.py
│   ├── change_detector.py
│   ├── database.py
│   └── scanner.py
|
├── scripts/
│
├── tests/
│   └── test_change_detector.py
|
├── .gitignore
├── pytest.ini
├── README.md
└── requirements.txt
```

---

## Current Application Flow

When HomeOps-AI runs:

```text
Start HomeOps-AI
      |
      v
Initialize SQLite database
      |
      v
Run network scan
      |
      v
Retrieve previous device state
      |
      v
Compare old state with new state
      |
      +----------------------+
      |                      |
      v                      v
Detect changes        Update inventory
      |                      |
      +----------+-----------+
                 |
                 v
        Record scan history
                 |
                 v
        Display network status
```

This architecture allows HomeOps-AI to maintain state between scans instead of treating each network scan independently.

---

## Device Inventory

HomeOps-AI maintains a persistent SQLite device inventory.

Each device can contain:

```text
IP Address
MAC Address
Hostname
Vendor
First Seen
Last Seen
Status
```

Devices are primarily identified using their MAC address so HomeOps-AI can recognize a known device even if DHCP assigns it a different IP address.

---

## Network Change Detection

HomeOps-AI compares the current network state against previously stored device information.

The system currently detects:

```text
NEW DEVICE
STATUS CHANGE
IP ADDRESS CHANGE
```

Example:

```text
Network Changes
--------------------------------------------------
[NEW DEVICE] laptop (192.168.1.45)

[STATUS CHANGE] ubuntu-server:
ONLINE -> OFFLINE

[IP CHANGE] desktop:
192.168.1.20 -> 192.168.1.37
```

If nothing changed:

```text
Network Changes
--------------------------------------------------
No network changes detected.
```

---

## Historical Telemetry

HomeOps-AI stores historical scan information separately from the current device inventory.

Each scan can record:

```text
Device
Timestamp
IP Address
Status
Latency
```

This historical telemetry will eventually support:

- Uptime analysis
- Latency monitoring
- Network health trends
- Dashboard visualizations
- Security event correlation
- AI-assisted network analysis

---

## Running HomeOps-AI

Clone the repository:

```bash
git clone https://github.com/GabrielBGN/HomeOps-AI.git
cd HomeOps-AI
```

### Windows

Create a virtual environment:

```powershell
py -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

Run HomeOps-AI:

```powershell
python -m homeops
```

### Linux / Raspberry Pi

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Run HomeOps-AI:

```bash
python -m homeops
```

---

## Example Output

```text
HomeOps-AI
============================================================
Starting network scan...

IP ADDRESS        HOSTNAME              STATUS
--------------------------------------------------
192.168.1.1       gateway               ONLINE
192.168.1.20      desktop               ONLINE
192.168.1.30      ubuntu-server         OFFLINE
--------------------------------------------------
Known devices: 3
Online: 2
Offline: 1

Network Changes
--------------------------------------------------
No network changes detected.
```

---

## Testing

HomeOps-AI uses `pytest` for automated testing.

Install pytest:

```bash
python -m pip install pytest
```

Run the test suite:

```bash
pytest
```

Current tests validate:

```text
New device detection
Device status changes
IP address changes
No-change behavior
```

Expected result:

```text
4 passed
```

---

## Configuration

Example configuration is stored in:

```text
config/config.example.yaml
```

Example:

```yaml
network:
  subnet: "192.168.1.0/24"
  scan_interval: 300

database:
  path: "data/homeops.db"

monitoring:
  timeout: 1
  new_device_alerts: true
```

The example configuration contains placeholder network information.

Machine-specific configuration and sensitive information should not be committed to the repository.

---

## Technology Stack

```text
Raspberry Pi 4
Python
Linux
SQLite
Git / GitHub
pytest
YAML

Planned:
Ansible
Docker
Prometheus
Grafana
Suricata
AI / LLM integration
```

---

## Development Roadmap

### V1 - Network Monitor

Current focus:

```text
[x] SQLite device inventory
[x] Persistent device state
[x] Network change detection
[x] Historical scan telemetry
[x] Latency telemetry structure
[x] Automated tests
[x] Mock network scanner
[ ] Raspberry Pi deployment
[ ] Real LAN device discovery
[ ] Real latency measurement
[ ] Hostname resolution
[ ] MAC address discovery
```

### V2 - Monitoring Dashboard

Planned features:

```text
Web dashboard
Device status overview
Latency graphs
Uptime history
Network event timeline
```

### V3 - Network Intelligence

Planned features:

```text
Automatic network change reports
Unknown-device alerts
Network health analytics
Automatic topology generation
```

### V4 - Infrastructure Automation

Planned integrations:

```text
Ansible
SSH automation
Linux administration
Configuration backups
Automated health checks
```

### V5 - Cybersecurity Monitoring

Planned capabilities:

```text
Centralized security logging
Suricata integration
Authentication monitoring
Network anomaly detection
Security alerts
```

### V6 - AI-Assisted Network Operations

Planned AI capabilities:

```text
"What changed on my network today?"

"Why is my server offline?"

"Summarize network problems from the last 24 hours."

"Explain this security alert."

"Which devices have experienced abnormal latency?"
```

The AI layer will use data collected by HomeOps-AI rather than functioning as a standalone chatbot.

---

## Security

HomeOps-AI does not commit sensitive information such as:

```text
Passwords
API keys
SSH private keys
Authentication tokens
Wi-Fi credentials
Private configuration files
Local SQLite databases
```

Sensitive files are excluded using `.gitignore`.

---

## Project Goal

HomeOps-AI is intended to function as a miniature home Network Operations Center and Security Operations Center.

The project is designed to provide hands-on experience with:

```text
Network Engineering
Linux Administration
Python Development
Network Monitoring
Cybersecurity
Infrastructure Automation
Databases
Observability
AI-Assisted Operations
```

The Raspberry Pi will eventually serve as the always-on HomeOps-AI node responsible for continuously monitoring and analyzing the home network.
