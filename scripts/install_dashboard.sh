
#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="/home/gab1010/HomeOps-AI"
SERVICE_NAME="homeops-dashboard.service"

SOURCE_FILE="$PROJECT_DIR/config/$SERVICE_NAME"
TARGET_FILE="/etc/systemd/system/$SERVICE_NAME"

echo "================================="
echo " HomeOps-AI Dashboard Installer"
echo "================================="

# Verify the dashboard exists
if [ ! -f "$PROJECT_DIR/homeops/dashboard.py" ]; then
    echo "ERROR: Dashboard Python file not found."
    exit 1
fi

# Verify the service configuration exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo "ERROR: Dashboard service file not found."
    exit 1
fi

echo "[1/4] Installing systemd service..."

sudo install -m 0644 "$SOURCE_FILE" "$TARGET_FILE"

echo "[2/4] Reloading systemd..."

sudo systemctl daemon-reload

echo "[3/4] Enabling and starting dashboard..."

sudo systemctl enable --now "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "[4/4] Checking service status..."

sudo systemctl status "$SERVICE_NAME" --no-pager

echo ""
echo "Dashboard installation complete!"
echo ""

PI_IP=$(hostname -I | awk '{print $1}')

echo "Open your dashboard at:"
echo "http://$PI_IP:8080"
