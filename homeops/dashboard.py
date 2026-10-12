
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape

from .database import initialize_database, get_all_devices

HOST = "0.0.0.0"
PORT = 8080


def build_dashboard():
    devices = get_all_devices()

    online = sum(1 for d in devices if d[6] == "ONLINE")
    offline = sum(1 for d in devices if d[6] == "OFFLINE")

    rows = ""

    for device in devices:
        ip, mac, hostname, vendor, first_seen, last_seen, status, missed = device

        status_class = "online" if status == "ONLINE" else "offline"

        rows += f"""
        <tr>
            <td>{escape(str(hostname or "Unknown"))}</td>
            <td>{escape(str(ip or "N/A"))}</td>
            <td>{escape(str(mac or "N/A"))}</td>
            <td>{escape(str(vendor or "Unknown"))}</td>
            <td><span class="{status_class}">{escape(str(status))}</span></td>
            <td>{escape(str(last_seen or "N/A"))}</td>
        </tr>
        """

    if not devices:
        rows = '<tr><td colspan="6">No devices found yet.</td></tr>'

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="refresh" content="30">
        <title>HomeOps-AI Dashboard</title>

        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #0f172a;
                color: #f8fafc;
                margin: 0;
                padding: 30px;
            }}

            h1 {{ color: #38bdf8; }}

            .stats {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin: 30px 0;
            }}

            .card {{
                background: #1e293b;
                padding: 20px;
                border-radius: 10px;
                min-width: 150px;
            }}

            .number {{
                font-size: 32px;
                font-weight: bold;
                margin-top: 10px;
            }}

            .table-container {{ overflow-x: auto; }}

            table {{
                width: 100%;
                border-collapse: collapse;
                background: #1e293b;
            }}

            th, td {{
                padding: 14px;
                border-bottom: 1px solid #334155;
                text-align: left;
            }}

            th {{ color: #38bdf8; }}

            .online {{ color: #4ade80; font-weight: bold; }}
            .offline {{ color: #f87171; font-weight: bold; }}

            .footer {{
                margin-top: 25px;
                color: #94a3b8;
                font-size: 13px;
            }}
        </style>
    </head>

    <body>
        <h1>HomeOps-AI</h1>
        <p>Network Monitoring Dashboard</p>

        <div class="stats">
            <div class="card">
                Total Devices
                <div class="number">{len(devices)}</div>
            </div>

            <div class="card">
                Online
                <div class="number">{online}</div>
            </div>

            <div class="card">
                Offline
                <div class="number">{offline}</div>
            </div>
        </div>

        <h2>Network Inventory</h2>

        <div class="table-container">
            <table>
                <tr>
                    <th>Hostname</th>
                    <th>IP Address</th>
                    <th>MAC Address</th>
                    <th>Vendor</th>
                    <th>Status</th>
                    <th>Last Seen</th>
                </tr>
                {rows}
            </table>
        </div>

        <div class="footer">
            Dashboard refreshes every 30 seconds.
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
            self.send_error(500, "Dashboard data unavailable")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)


def main():
    initialize_database()

    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)

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
