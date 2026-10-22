
"""Web dashboard for HomeOps-AI."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape
from urllib.parse import parse_qs

from .database import (
    initialize_database,
    get_all_devices,
    get_recent_scan_history,
    get_device_availability,
    get_recent_alerts,
    get_unread_alert_count,
    mark_alert_read,
)

HOST = "0.0.0.0"
PORT = 8080


def safe_text(value, default="N/A"):
    """Escape database values before displaying them in HTML."""
    if value is None or value == "":
        return default
    return escape(str(value))


def normalize_status(status):
    """Normalize device status regardless of letter case."""
    return str(status or "UNKNOWN").strip().upper()


def build_dashboard():
    """Build the HomeOps-AI dashboard HTML."""

    devices = get_all_devices()
    history = get_recent_scan_history(limit=20)
    alerts = get_recent_alerts(limit=30)
    unread_count = get_unread_alert_count()
    availability = get_device_availability()

    online = sum(
        1 for device in devices
        if normalize_status(device[6]) == "ONLINE"
    )

    offline = sum(
        1 for device in devices
        if normalize_status(device[6]) == "OFFLINE"
    )

    # ---------------------------------------------
    # NETWORK INVENTORY
    # ---------------------------------------------

    device_rows = ""

    for device in devices:
        (
            ip,
            mac,
            hostname,
            vendor,
            first_seen,
            last_seen,
            status,
            missed,
        ) = device

        normalized_status = normalize_status(status)

        status_class = (
            "online"
            if normalized_status == "ONLINE"
            else "offline"
        )

        device_rows += f"""
        <tr>
            <td>{safe_text(hostname, "Unknown")}</td>
            <td>{safe_text(ip)}</td>
            <td>{safe_text(mac)}</td>
            <td>{safe_text(vendor, "Unknown")}</td>
            <td>
                <span class="{status_class}">
                    {safe_text(normalized_status)}
                </span>
            </td>
            <td>{safe_text(last_seen)}</td>
        </tr>
        """

    if not devices:
        device_rows = """
        <tr>
            <td colspan="6">No devices discovered yet.</td>
        </tr>
        """

    # ---------------------------------------------
    # NETWORK ANALYTICS (HomeOps-AI v1.2.0)
    # ---------------------------------------------

    availability_rows = ""

    for device in availability:
        observed_count = device["total_observations"]
        availability_pct = device["availability_pct"]
        availability_text = (
            f"{availability_pct:.2f}%"
            if availability_pct is not None
            else "N/A"
        )
        normalized_status = normalize_status(device["status"])
        status_class = (
            "online" if normalized_status == "ONLINE" else "offline"
        )

        availability_rows += f"""
        <tr>
            <td>{safe_text(device["hostname"], "Unknown")}</td>
            <td>{safe_text(device["ip_address"])}</td>
            <td><span class="{status_class}">{safe_text(normalized_status)}</span></td>
            <td>{availability_text}</td>
            <td>{int(device["seen_count"])}</td>
            <td>{int(device["missed_count"])}</td>
            <td>{int(observed_count)}</td>
        </tr>
        """

    if not availability:
        availability_rows = """
        <tr><td colspan="7">No devices discovered yet.</td></tr>
        """

    # ---------------------------------------------
    # NETWORK ALERTS
    # ---------------------------------------------

    alert_rows = ""

    alert_labels = {
        "NEW_DEVICE": "Security Alert",
        "DEVICE_OFFLINE": "Device Offline",
        "DEVICE_ONLINE": "Device Reconnected",
    }

    alert_classes = {
        "NEW_DEVICE": "alert-security",
        "DEVICE_OFFLINE": "alert-offline",
        "DEVICE_ONLINE": "alert-recovery",
    }

    for alert in alerts:
        alert_type = alert["alert_type"]

        alert_label = alert_labels.get(
            alert_type,
            "Network Event"
        )

        alert_class = alert_classes.get(
            alert_type,
            "alert-default"
        )

        read_class = (
            "read-alert"
            if alert["is_read"]
            else "unread-alert"
        )

        if alert["is_read"]:
            action_html = '<span class="read-status">Read</span>'
        else:
            alert_id = int(alert["id"])

            action_html = f"""
            <form method="POST" action="/alerts/read">
                <input
                    type="hidden"
                    name="alert_id"
                    value="{alert_id}"
                >
                <button type="submit" class="read-button">
                    Mark as Read
                </button>
            </form>
            """

        alert_rows += f"""
        <tr class="{read_class}">
            <td>{safe_text(alert["created_at"])}</td>
            <td>
                <span class="alert-badge {alert_class}">
                    {safe_text(alert_label)}
                </span>
            </td>
            <td>{safe_text(alert["message"])}</td>
            <td>{safe_text(alert["mac_address"])}</td>
            <td>{action_html}</td>
        </tr>
        """

    if not alerts:
        alert_rows = """
        <tr>
            <td colspan="5">
                No network alerts recorded yet.
            </td>
        </tr>
        """

    # ---------------------------------------------
    # SCAN HISTORY
    # ---------------------------------------------

    history_rows = ""

    for record in history:
        hostname = record.get("hostname")
        ip = record.get("ip_address")
        status = record.get("status")
        latency = record.get("latency_ms")
        timestamp = record.get("timestamp")

        normalized_status = normalize_status(status)

        status_class = (
            "online"
            if normalized_status == "ONLINE"
            else "offline"
        )

        if isinstance(latency, (int, float)):
            latency_text = f"{latency:.1f} ms"
        else:
            latency_text = "N/A"

        history_rows += f"""
        <tr>
            <td>{safe_text(timestamp)}</td>
            <td>{safe_text(hostname, "Unknown")}</td>
            <td>{safe_text(ip)}</td>
            <td>
                <span class="{status_class}">
                    {safe_text(normalized_status)}
                </span>
            </td>
            <td>{latency_text}</td>
        </tr>
        """

    if not history:
        history_rows = """
        <tr>
            <td colspan="5">No scan history available.</td>
        </tr>
        """

    # ---------------------------------------------
    # DASHBOARD HTML
    # ---------------------------------------------

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1">
        <meta http-equiv="refresh" content="30">

        <title>HomeOps-AI Dashboard</title>

        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                font-family: Arial, sans-serif;
                background: #0f172a;
                color: #f8fafc;
                margin: 0;
                padding: 30px;
            }}

            h1 {{
                color: #38bdf8;
                margin-bottom: 5px;
            }}

            h2 {{
                margin-top: 35px;
            }}

            .subtitle {{
                color: #94a3b8;
            }}

            .stats {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin: 30px 0;
            }}

            .card {{
                background: #1e293b;
                padding: 22px;
                border-radius: 10px;
                flex: 1;
                min-width: 150px;
            }}

            .card-label {{
                color: #94a3b8;
                font-size: 14px;
            }}

            .number {{
                font-size: 32px;
                font-weight: bold;
                margin-top: 10px;
            }}

            .table-container {{
                overflow-x: auto;
                background: #1e293b;
                border-radius: 10px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th, td {{
                padding: 14px;
                text-align: left;
                border-bottom: 1px solid #334155;
                white-space: nowrap;
            }}

            th {{
                color: #38bdf8;
                background: #1e293b;
            }}

            tr:hover {{
                background: #334155;
            }}

            .online {{
                color: #4ade80;
                font-weight: bold;
            }}

            .offline {{
                color: #f87171;
                font-weight: bold;
            }}

            .alert-badge {{
                display: inline-block;
                padding: 6px 10px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }}

            .alert-security {{
                color: #fca5a5;
                background: #7f1d1d;
            }}

            .alert-offline {{
                color: #fdba74;
                background: #7c2d12;
            }}

            .alert-recovery {{
                color: #86efac;
                background: #14532d;
            }}

            .alert-default {{
                color: #cbd5e1;
                background: #334155;
            }}

            .unread-alert {{
                background: #263449;
                font-weight: bold;
            }}

            .read-alert {{
                color: #94a3b8;
            }}

            .read-status {{
                font-size: 12px;
                font-weight: bold;
            }}

            .read-button {{
                background: #0284c7;
                color: #ffffff;
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: bold;
                cursor: pointer;
                white-space: nowrap;
            }}

            .read-button:hover {{
                background: #0369a1;
            }}

            .alert-count {{
                color: #fbbf24;
            }}

            .footer {{
                margin-top: 30px;
                color: #94a3b8;
                font-size: 13px;
            }}

            @media (max-width: 600px) {{
                body {{
                    padding: 15px;
                }}
            }}
        </style>
    </head>

    <body>
        <h1>HomeOps-AI</h1>
        <p class="subtitle">
            Raspberry Pi Network Monitoring Dashboard
        </p>

        <div class="stats">
            <div class="card">
                <div class="card-label">Total Devices</div>
                <div class="number">{len(devices)}</div>
            </div>

            <div class="card">
                <div class="card-label">Online Devices</div>
                <div class="number online">{online}</div>
            </div>

            <div class="card">
                <div class="card-label">Offline Devices</div>
                <div class="number offline">{offline}</div>
            </div>

            <div class="card">
                <div class="card-label">Unread Alerts</div>
                <div class="number alert-count">
                    {unread_count}
                </div>
            </div>
        </div>

        <h2>Network Alerts</h2>
        <p class="subtitle">
            Latest 30 network events and security notifications
        </p>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Alert Type</th>
                        <th>Message</th>
                        <th>MAC Address</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {alert_rows}
                </tbody>
            </table>
        </div>

        <h2>Network Inventory</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Hostname</th>
                        <th>IP Address</th>
                        <th>MAC Address</th>
                        <th>Vendor</th>
                        <th>Status</th>
                        <th>Last Seen</th>
                    </tr>
                </thead>
                <tbody>
                    {device_rows}
                </tbody>
            </table>
        </div>

        <h2>Network Analytics: Device Availability</h2>
        <p class="subtitle">
            Percentage of recorded scans in which each device was seen.
            A missed discovery response does not necessarily mean a device
            was disconnected. N/A means no observations have been recorded.
            Historical observations begin when v1.2.0 tracking is enabled.
        </p>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Hostname</th>
                        <th>IP Address</th>
                        <th>Current Status</th>
                        <th>Observed Availability</th>
                        <th>Seen</th>
                        <th>Missed</th>
                        <th>Total Observations</th>
                    </tr>
                </thead>
                <tbody>
                    {availability_rows}
                </tbody>
            </table>
        </div>

        <h2>Recent Scan History</h2>
        <p class="subtitle">
            Latest 20 recorded device scan results
        </p>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Device</th>
                        <th>IP Address</th>
                        <th>Status</th>
                        <th>Latency</th>
                    </tr>
                </thead>
                <tbody>
                    {history_rows}
                </tbody>
            </table>
        </div>

        <div class="footer">
            Dashboard automatically refreshes every 30 seconds.
        </div>
    </body>
    </html>
    """


class DashboardHandler(BaseHTTPRequestHandler):
    """Serve the HomeOps-AI dashboard."""

    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return

        try:
            page = build_dashboard().encode("utf-8")
        except Exception:
            self.send_error(
                500,
                "Dashboard data unavailable"
            )
            return

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(page))
        )
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self):
        """Mark a single alert as read."""

        if self.path != "/alerts/read":
            self.send_error(404)
            return

        content_type = self.headers.get(
            "Content-Type", ""
        )

        if content_type.split(";")[0].strip().lower() != (
            "application/x-www-form-urlencoded"
        ):
            self.send_error(415, "Unsupported content type")
            return

        try:
            content_length = int(
                self.headers.get("Content-Length", "0")
            )
        except ValueError:
            self.send_error(400, "Invalid content length")
            return

        if not 0 < content_length <= 1024:
            self.send_error(400, "Invalid request size")
            return

        body = self.rfile.read(content_length)

        try:
            form = parse_qs(
                body.decode("utf-8"),
                strict_parsing=True,
            )

            alert_ids = form.get("alert_id", [])

            if len(alert_ids) != 1:
                raise ValueError("Invalid alert ID")

            alert_id_text = alert_ids[0]

            if not alert_id_text.isascii() or not (
                alert_id_text.isdecimal()
            ):
                raise ValueError("Invalid alert ID")

            alert_id = int(alert_id_text)

            if alert_id <= 0:
                raise ValueError("Invalid alert ID")

        except (UnicodeDecodeError, ValueError):
            self.send_error(400, "Invalid alert ID")
            return

        try:
            updated = mark_alert_read(alert_id)
        except Exception:
            self.send_error(
                500,
                "Unable to update alert"
            )
            return

        if not updated:
            self.send_error(404, "Alert not found")
            return

        self.send_response(303)
        self.send_header("Location", "/")
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()


def main():
    """Start the HomeOps-AI dashboard server."""
    initialize_database()

    server = ThreadingHTTPServer(
        (HOST, PORT),
        DashboardHandler
    )

    print(f"HomeOps-AI Dashboard running on port {PORT}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
