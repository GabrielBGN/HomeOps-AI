
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape

from .database import (
    initialize_database,
    get_all_devices,
    get_recent_scan_history,
)

HOST = "0.0.0.0"
PORT = 8080


def safe_text(value, default="N/A"):
    if value is None or value == "":
        return default
    return escape(str(value))


def build_dashboard():
    devices = get_all_devices()
    history = get_recent_scan_history(limit=20)

    online = sum(
        1 for device in devices
        if device[6] == "ONLINE"
    )

    offline = sum(
        1 for device in devices
        if device[6] == "OFFLINE"
    )

    # Build the device inventory table
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

        status_class = (
            "online" if status == "ONLINE" else "offline"
        )

        device_rows += f"""
        <tr>
            <td>{safe_text(hostname, "Unknown")}</td>
            <td>{safe_text(ip)}</td>
            <td>{safe_text(mac)}</td>
            <td>{safe_text(vendor, "Unknown")}</td>
            <td>
                <span class="{status_class}">
                    {safe_text(status)}
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

    # Build the recent scan history table
    history_rows = ""

    for record in history:
        hostname = record.get("hostname")
        ip = record.get("ip_address")
        status = record.get("status")
        latency = record.get("latency_ms")
        timestamp = record.get("timestamp")

        status_class = (
            "online" if status == "ONLINE" else "offline"
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
                    {safe_text(status)}
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
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)


def main():
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
