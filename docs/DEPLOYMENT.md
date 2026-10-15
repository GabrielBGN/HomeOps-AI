
# HomeOps-AI Deployment Guide

This guide explains how to deploy and verify HomeOps-AI
on a Raspberry Pi 4 running Raspberry Pi OS.

## Environment

- Device: Raspberry Pi 4
- Operating system: Raspberry Pi OS Bullseye
- Python: 3.9 or newer
- Project directory: `/home/gab1010/HomeOps-AI`
- Dashboard port: `8080`

## 1. Connect to the Raspberry Pi

Connect to the Raspberry Pi using SSH:

```bash
ssh gab1010@192.168.1.109
```

The IP address may change depending on the router's
DHCP configuration.

## 2. Update HomeOps-AI

Navigate to the project directory:

```bash
cd /home/gab1010/HomeOps-AI
```

Check for uncommitted changes:

```bash
git status
```

If there are no local changes that need to be saved,
download the latest code:

```bash
git pull --ff-only
```

Do not discard uncommitted changes.

## 3. Run a network scan

Before configuring trusted devices, run a manual scan:

```bash
python3 -m homeops
```

The scanner should discover devices and update the
SQLite inventory.

Review the output for errors.

The Security Review may display a message indicating
that trusted-device configuration is missing. This
is expected during initial setup.

## 4. Configure trusted devices

HomeOps-AI supports interactive trusted-device setup.

First, check whether the private configuration
already exists:

```bash
ls -l config/trusted_devices.json
```

### Option A: Interactive setup (recommended)

If the configuration file does not exist, run:

```bash
python3 -m homeops.trust_setup
```

The tool reads discovered devices from the database
and displays their details.

For each device:

1. Review the hostname, IP address, and MAC address.
2. Enter `y` to trust a recognized device.
3. Enter `n` to skip an unrecognized device.
4. Type `YES` at the final confirmation prompt.

The tool creates:

```text
config/trusted_devices.json
```

The file is created with owner-only permissions.

The tool will not overwrite an existing configuration.

Only approve devices you recognize and authorize.

### Option B: Manual configuration

If the configuration file already exists, review
and edit it instead:

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

Replace these example MAC addresses with the actual
addresses of trusted devices.

If creating the file manually for the first time,
you may copy the example:

```bash
cp -n config/trusted_devices.example.json \
  config/trusted_devices.json
```

After manually creating the file, restrict access:

```bash
chmod 600 config/trusted_devices.json
```

Important:

- Never commit the private configuration to GitHub.
- An empty trusted list flags every discovered online
  device with a valid MAC address.
- Some devices use randomized MAC addresses.
- MAC addresses can be spoofed.
- An unrecognized device is not automatically malicious.

Validate the JSON:

```bash
python3 -m json.tool \
  config/trusted_devices.json
```

## 5. Run deployment preflight

After configuring trusted devices, run:

```bash
python3 -m homeops.preflight
```

The preflight checker verifies:

- Python version
- Required project files
- Private trusted-device configuration
- Trusted MAC address validity

Example successful output:

```text
HomeOps-AI Deployment Preflight
============================================================
[PASS] Python 3.9
[PASS] Found homeops/__main__.py
...
[PASS] Trusted-device configuration is valid (5 devices)
------------------------------------------------------------
Preflight passed with 0 warning(s).
```

This is illustrative output.

A `FAIL` means a deployment prerequisite needs
attention.

A `WARN` means deployment may proceed, but the
reported issue should be reviewed.

Preflight does not test live network connectivity,
systemd services, or dashboard accessibility.

## 6. Verify security monitoring

Run another manual scan:

```bash
python3 -m homeops
```

Confirm that the output includes:

- Device inventory
- Online and offline counts
- Network changes
- Security Review
- Scan complete

Review any unrecognized devices.

Do not automatically trust an unfamiliar device
just to clear a security warning.

## 7. Install the dashboard

Run the dashboard installer:

```bash
bash scripts/install_dashboard.sh
```

Verify the service:

```bash
sudo systemctl status \
  homeops-dashboard.service --no-pager
```

Open the dashboard from a browser connected to
the home network:

```text
http://192.168.1.109:8080
```

Replace the IP address if it has changed.

Security note:

The dashboard currently has no authentication.
Do not forward port 8080 through your router or
expose the dashboard directly to the internet.

## 8. Verify automatic network scanning

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

Review recent scanner logs:

```bash
sudo journalctl -u homeops.service \
  -n 50 --no-pager
```

The timer should continue triggering network scans
automatically.

## 9. Troubleshooting

### Scanner fails

Run the scanner manually:

```bash
python3 -m homeops
```

Review the traceback or error message.

### Dashboard does not load

Check the dashboard service:

```bash
sudo systemctl status \
  homeops-dashboard.service --no-pager
```

Review its logs:

```bash
sudo journalctl -u homeops-dashboard.service \
  -n 50 --no-pager
```

### Trusted-device setup refuses to run

The interactive tool does not overwrite an existing
trusted-device configuration.

Check for:

```text
config/trusted_devices.json
```

If it exists, review and edit it manually.

### No devices appear during setup

Run a network scan:

```bash
python3 -m homeops
```

Then retry interactive setup if the configuration
file does not already exist.

### Preflight fails

Read each `FAIL` message.

Check missing files, Python compatibility, and
trusted-device configuration.

### Raspberry Pi IP address changed

Find the current address:

```bash
hostname -I
```

Use the current IP address when connecting to
SSH or the dashboard.

## 10. Deployment verification checklist

- [ ] Latest GitHub changes pulled
- [ ] Manual network scan successful
- [ ] Trusted devices reviewed and approved
- [ ] Private trusted-device configuration created
- [ ] JSON configuration validated
- [ ] Deployment preflight passed
- [ ] Security Review verified
- [ ] Dashboard service running
- [ ] Dashboard accessible from the home network
- [ ] Automatic scanner timer active
- [ ] Scanner logs checked
- [ ] No unexpected errors

## Deployment status

GitHub Actions validates the project's automated tests.

Raspberry Pi deployment and real-network verification
must still be completed locally.

Do not assume successful GitHub tests guarantee that
the live Raspberry Pi deployment is working.
