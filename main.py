"""
Dawit Telecom - Enterprise Network Monitor & Self-Healing Engine
Author: Dawit
Architecture: Multi-threaded, Zero-Crash Exception Handling, Injection Protected,
              SSH RSA Healing, Dynamic DB Inventory, Telegram Inline Buttons & SMS Fallback.
"""

import os
import time
import shutil
import re
import subprocess
import ipaddress
import logging
import requests
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from database import init_db, get_active_inventory, log_ping_result, archive_old_logs, get_db_connection

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MY_PHONE_NUMBER = os.getenv("MY_PHONE_NUMBER", "+251900000000")
SSH_KEY_PATH = os.path.expanduser(os.getenv("SSH_KEY_PATH", "~/.ssh/id_rsa"))

FAIL_COUNTS = {}
SSH_COOLDOWN = {}
THRESHOLD = 3
COOLDOWN_SECONDS = 900

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def is_valid_ip(ip_str):
    try:
        ipaddress.ip_address(ip_str.strip())
        return True
    except ValueError:
        return False


def send_telegram_alert(message, silent=False, reply_markup=None):
    if not BOT_TOKEN or not CHAT_ID:
        return

    try:
        token = BOT_TOKEN.strip().replace("bot", "") if BOT_TOKEN.startswith("bot") else BOT_TOKEN.strip()
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        payload = {
            "chat_id": CHAT_ID.strip(),
            "text": message,
            "parse_mode": "HTML",
            "disable_notification": silent
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logging.error(f"Telegram Alert Dispatch Exception: {e}")


def get_inline_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "📊 Live Status", "callback_data": "/status"},
                {"text": "❓ Help Menu", "callback_data": "/help"}
            ]
        ]
    }


def send_sms_alert(message):
    """Graceful SMS Dispatcher with Termux and Twilio Fallback."""
    logging.info(f"📱 Dispatching SMS Alert to {MY_PHONE_NUMBER}...")

    # Termux API (Local Phone)
    if shutil.which("termux-sms-send"):
        try:
            res = subprocess.run(["termux-sms-send", "-n", MY_PHONE_NUMBER, message], capture_output=True, text=True)
            if res.returncode == 0:
                logging.info("✅ SMS sent via Termux API!")
                return
        except Exception as e:
            logging.error(f"Termux SMS Error: {e}")

    # Twilio API (PC Mode)
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    if sid and auth_token and from_number:
        try:
            from twilio.rest import Client
            client = Client(sid, auth_token)
            client.messages.create(body=message, from_=from_number, to=MY_PHONE_NUMBER)
            logging.info("✅ SMS sent via Twilio Cloud API!")
        except Exception as e:
            logging.error(f"Twilio API Error: {e}")


def ping_host(ip):
    """Executes ICMP ping with Command-Injection Protection & Latency Calculation."""
    if not is_valid_ip(ip):
        return False, None

    try:
        # Secure Subprocess execution without shell=True
        res = subprocess.run(["ping", "-c", "2", ip], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            match = re.search(r"time[=s]([\d\.]+)\s*ms", res.stdout)
            latency = float(match.group(1)) if match else 10.0
            return True, latency
        return False, None
    except Exception:
        return False, None


def try_ssh_self_healing(ip):
    """SSH Key-Based Remote Recovery with Cooldown Control."""
    now = time.time()
    if ip in SSH_COOLDOWN and (now - SSH_COOLDOWN[ip]) < COOLDOWN_SECONDS:
        return "⏳ SSH Healing in Cooldown (Skipped)."

    SSH_COOLDOWN[ip] = now
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if os.path.exists(SSH_KEY_PATH):
            key = paramiko.RSAKey.from_private_key_file(SSH_KEY_PATH)
            ssh.connect(ip, username="admin", pkey=key, timeout=5)
            ssh.exec_command("sudo systemctl restart nginx")
            ssh.close()
            return "⚡ SSH Remote Command Transmitted (RSA Auth)."
        else:
            return "⚡ Simulated SSH Service Recovery Executed (Simulation)."
    except Exception as e:
        return f"⚡ SSH Healing Simulated (Notice: {e})"


def check_single_host(ip, label):
    """Worker Thread Task."""
    try:
        is_online, latency = ping_host(ip)
        status = "ONLINE" if is_online else "OFFLINE"

        log_ping_result(ip, status, latency)

        if is_online:
            FAIL_COUNTS[ip] = 0
            return {"ip": ip, "label": label, "status": "ONLINE", "latency": latency, "alert": False}
        else:
            FAIL_COUNTS[ip] = FAIL_COUNTS.get(ip, 0) + 1
            should_alert = FAIL_COUNTS[ip] == THRESHOLD
            ssh_msg = try_ssh_self_healing(ip) if should_alert else ""
            return {"ip": ip, "label": label, "status": "OFFLINE", "latency": None, "alert": should_alert, "ssh": ssh_msg}
    except Exception as e:
        logging.error(f"Error checking host {ip}: {e}")
        return {"ip": ip, "label": label, "status": "OFFLINE", "latency": None, "alert": False, "ssh": ""}


def execute_network_scan():
    """Concurrent Multi-threaded Scanner."""
    inventory = get_active_inventory()
    logging.info(f"🌐 [Scan Triggered] Testing {len(inventory)} hosts in parallel...")

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_single_host, ip, label) for ip, label in inventory.items()]
        for future in futures:
            try:
                results.append(future.result())
            except Exception as e:
                logging.error(f"Thread execution error: {e}")

    critical_failures = [r for r in results if r and r.get("alert")]
    if critical_failures:
        msg = "🚨 <b>CRITICAL NETWORK ALERT!</b>\n\n"
        for item in critical_failures:
            msg += f"❌ <code>{item['ip']}</code> ({item['label']}) is <b>DOWN</b>!\n"
            if item.get("ssh"):
                msg += f"🔧 {item['ssh']}\n"

        send_telegram_alert(msg, silent=False, reply_markup=get_inline_keyboard())
        send_sms_alert(f"CRITICAL: {len(critical_failures)} Network Nodes DOWN!")


def handle_telegram_updates(last_update_id):
    """Telegram Polling and Callback Query Engine."""
    if not BOT_TOKEN:
        return last_update_id

    try:
        token = BOT_TOKEN.strip().replace("bot", "") if BOT_TOKEN.startswith("bot") else BOT_TOKEN.strip()
        url = f"https://api.telegram.org/bot{token}/getUpdates"

        res = requests.get(url, params={"offset": last_update_id + 1, "timeout": 2}, timeout=5)
        if res.status_code == 200:
            updates = res.json().get("result", [])
            for update in updates:
                last_update_id = update["update_id"]

                cmd = ""
                if "callback_query" in update:
                    cmd = update["callback_query"].get("data", "")
                elif "message" in update:
                    cmd = update["message"].get("text", "").strip()

                raw_cmd = cmd.lower().split('@')[0]

                if raw_cmd == "/status":
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT i.ip_address, i.label, l.status, l.latency_ms
                            FROM ip_inventory i LEFT JOIN ping_logs l ON i.ip_address = l.ip_address
                            WHERE l.id IN (SELECT MAX(id) FROM ping_logs GROUP BY ip_address) OR l.id IS NULL
                        """)
                        rows = cursor.fetchall()
                        conn.close()

                        msg = "📊 <b>CURRENT NETWORK STATUS</b>\n\n"
                        for r in rows:
                            icon = "✅" if r["status"] == "ONLINE" else "❌"
                            lat = f"({r['latency_ms']} ms)" if r["latency_ms"] else ""
                            msg += f"{icon} <code>{r['ip_address']}</code> - {r['label']} <b>{r['status']}</b> {lat}\n"

                        send_telegram_alert(msg, silent=True, reply_markup=get_inline_keyboard())

                elif raw_cmd in ["/help", "/start"]:
                    help_text = (
                        "🤖 <b>Dawit Telecom Monitor Help Menu</b>\n\n"
                        "📌 <b>/status</b> - Live Dynamic Network Health\n"
                        "📌 <b>/check &lt;IP&gt;</b> - On-demand IP test"
                    )
                    send_telegram_alert(help_text, silent=True, reply_markup=get_inline_keyboard())

                elif raw_cmd.startswith("/check"):
                    parts = cmd.split()
                    if len(parts) > 1:
                        target_ip = parts[1].strip()
                        if is_valid_ip(target_ip):
                            is_online, lat = ping_host(target_ip)
                            st = "ONLINE ✅" if is_online else "OFFLINE ❌"
                            lat_str = f"({lat} ms)" if lat else ""
                            send_telegram_alert(f"Result for <code>{target_ip}</code>: <b>{st}</b> {lat_str}")
                        else:
                            send_telegram_alert("❌ <b>Error:</b> Invalid IP address format.")
                    else:
                        send_telegram_alert("⚠️ Usage: <code>/check 8.8.8.8</code>")
    except Exception as e:
        logging.error(f"Telegram polling exception: {e}")

    return last_update_id


def main():
    logging.info("🚀 Starting Dawit Telecom Enterprise Suite...")
    init_db()
    send_telegram_alert("🤖 <b>Dawit Telecom Enterprise Engine Online!</b>", silent=True, reply_markup=get_inline_keyboard())

    last_update_id = 0
    scan_timer = time.time()

    while True:
        try:
            if time.time() - scan_timer > 30:
                execute_network_scan()
                archive_old_logs(days_threshold=30)
                scan_timer = time.time()

            last_update_id = handle_telegram_updates(last_update_id)
            time.sleep(1)
        except Exception as e:
            logging.error(f"Main loop exception safety triggered: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()
