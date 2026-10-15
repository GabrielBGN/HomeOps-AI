
# HomeOps-AI Deployment Guide

This guide explains how to deploy HomeOps-AI updates to a
Raspberry Pi 4 running Raspberry Pi OS.

## Environment

- Device: Raspberry Pi 4
- Operating system: Raspberry Pi OS Bullseye
- Python: 3.9
- Project directory: `/home/gab1010/HomeOps-AI`
- Dashboard port: `8080`

## 1. Connect to the Raspberry Pi

Open a terminal on a computer connected to the home network.

Connect using SSH:

```bash
ssh gab1010@192.168.1.109
```

The IP address may change if the router assigns a new one.

## 2. Update the repository

Navigate to the project:

```bash
cd /home/gab1010/HomeOps-AI
```

Check for uncommitted local changes:

```bash
git status
```

If there are no changes that need to be saved, pull the
latest code:

```bash
git pull --ff-only
```

Do not overwrite uncommitted work.

## 3. Configure trusted devices

Create the private trusted-device configuration:

```bash
cp -n config/trusted_devices.example.json \
  config/trusted_devices.json
```

Edit the configuration:

```bash
nano config/trusted_devices.json
```

Example:

```json
{
  "trusted_macs": [
    "AA:BB:CC:DD:EE:01",
    "AA:BB:CC:DD:EE:02"
  ]
}
```

Replace the example addresses with actual trusted
device MAC addresses.

Important:

- Keep this file private.
- Do not commit it to GitHub.
- An empty trusted list will cause every discovered
  online device with a valid MAC to be flagged.
- Some devices use randomized MAC addresses.

Validate the JSON:

```bash
python3 -m json.tool \
  config/trusted_devices.json
```

## 4. Test the network scanner

Run a manual scan:

```bash
python3 -m homeops
```

Check that the output includes:

- Device inventory
- Online and offline counts
- Network changes
- Security Review
- Scan complete

Review any unrecognized devices.

An unrecognized MAC address does not necessarily
indicate an intruder.

## 5. Install the dashboard service

Run the dashboard installer:

```bash
bash scripts/install_dashboard.sh
```

Verify the dashboard service:

```bash
sudo systemctl status \
  homeops-dashboard.service --no-pager
```

Check the dashboard in a browser on the home network:

```text
http://192.168.1.109:8080
```

Use the Raspberry Pi's current IP address if different.

Do not expose port 8080 directly to the internet.
The dashboard currently has no authentication.

## 6. Verify automatic scanning

Check the existing scanner timer:

```bash
sudo systemctl status \
  homeops.timer --no-pager
```

Check the scanner service:

```bash
sudo systemctl status \
  homeops.service --no-pager
```

View recent scanner logs:

```bash
sudo journalctl -u homeops.service \
  -n 50 --no-pager
```

The scanner should continue running automatically
through the systemd timer.

## 7. Troubleshooting

### Scanner fails

Run the scanner manually:

```bash
python3 -m homeops
```

Review the error output.

### Dashboard does not load

Check the service:

```bash
sudo systemctl status \
  homeops-dashboard.service --no-pager
```

Review its logs:

```bash
sudo journalctl -u homeops-dashboard.service \
  -n 50 --no-pager
```

### Security monitoring is skipped

Verify that this file exists:

```text
config/trusted_devices.json
```

Validate its JSON and check the MAC address formats.

### Dashboard IP address changed

Find the Raspberry Pi's current IP:

```bash
hostname -I
```

Use the correct address with port 8080.

## 8. Deployment verification checklist

- [ ] Latest GitHub changes pulled
- [ ] Trusted-device configuration created privately
- [ ] JSON configuration validated
- [ ] Manual network scan successful
- [ ] Security Review appears in scanner output
- [ ] Dashboard service running
- [ ] Dashboard accessible from home network
- [ ] Automatic scanner timer active
- [ ] Scanner logs checked
- [ ] No unexpected errors

## Deployment status

Code and automated tests are maintained through GitHub.

Raspberry Pi deployment and real-network verification
must be completed locally.
