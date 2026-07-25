"""
Dawit Telecom Enterprise Monitor - Web API Dashboard
Author: Dawit
Description: REST API & Visual Graphical Dashboard for live remote monitoring.
"""

import logging
from flask import Flask, jsonify, render_template_string
from database import get_db_connection

app = Flask(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dawit Telecom - Visual Monitor</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 25px; }
        h1 { color: #38bdf8; margin-bottom: 5px; }
        p { color: #94a3b8; font-size: 14px; margin-top: 0; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; margin-top: 20px; }
        .card { background: #1e293b; padding: 20px; border-radius: 10px; border-left: 6px solid #64748b; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .card.ONLINE { border-left-color: #22c55e; }
        .card.OFFLINE { border-left-color: #ef4444; }
        .status { font-weight: bold; font-size: 18px; }
        .ONLINE .status { color: #4ade80; }
        .OFFLINE .status { color: #f87171; }
        .meta { font-size: 12px; color: #64748b; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>🌐 Dawit Telecom Enterprise Visual Monitor</h1>
    <p>Live Real-Time Dashboard (Auto-refreshes every 10 seconds)</p>
    <div class="grid">
        {% for node in nodes %}
        <div class="card {{ node.status }}">
            <div><strong>{{ node.label }}</strong></div>
            <div style="font-family: monospace; font-size: 15px;">{{ node.ip_address }}</div>
            <div class="status" style="margin-top: 10px;">{{ node.status }}</div>
            <div>Latency: <strong>{{ node.latency_ms if node.latency_ms else 'N/A' }} ms</strong></div>
            <div class="meta">Last Checked: {{ node.timestamp if node.timestamp else 'Just Now' }}</div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    conn = get_db_connection()
    if not conn:
        return "Database Connection Unavailable", 500

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.ip_address, i.label, l.status, l.latency_ms, l.timestamp
            FROM ip_inventory i
            LEFT JOIN ping_logs l ON i.ip_address = l.ip_address
            WHERE l.id IN (SELECT MAX(id) FROM ping_logs GROUP BY ip_address) OR l.id IS NULL
        """)
        nodes = cursor.fetchall()
        return render_template_string(HTML_TEMPLATE, nodes=nodes)
    except Exception as e:
        return f"Error loading dashboard: {e}", 500
    finally:
        conn.close()

@app.route("/api/status")
def api_status():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database error"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ping_logs ORDER BY id DESC LIMIT 20")
        logs = [dict(row) for row in cursor.fetchall()]
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
