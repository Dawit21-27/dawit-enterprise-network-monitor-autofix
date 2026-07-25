"""
Dawit Telecom Enterprise Monitor - Database & Monthly Archiving Layer
Author: Dawit
Description: Thread-safe SQLite management, Dynamic Inventory, Latency Tracking,
             and Monthly Log Archiving to Year/Month folder structures.
"""

import os
import sqlite3
import csv
import logging
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "network_monitor.db")
ARCHIVE_DIR = os.path.join(BASE_DIR, "archives")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database Connection Error: {e}")
        return None


def init_db():
    """Initializes schema and seeds initial dynamic inventory safely."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Table 1: Dynamic IP Inventory
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                label TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Table 2: Ping & Latency History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ping_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL,
                status TEXT NOT NULL,
                latency_ms REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table 3: SSH Healing Event Tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS healing_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL,
                action_taken TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Default Seed Inventory
        default_ips = [
            ("8.8.8.8", "Google Primary DNS"),
            ("1.1.1.1", "Cloudflare DNS"),
            ("10.99.99.99", "Critical Core Router (Simulation)")
        ]
        for ip, label in default_ips:
            cursor.execute("INSERT OR IGNORE INTO ip_inventory (ip_address, label) VALUES (?, ?)", (ip, label))

        conn.commit()
        logging.info("✅ Database Layer & Schema Initialized Successfully!")
    except sqlite3.Error as e:
        logging.error(f"Database Initialization Error: {e}")
    finally:
        conn.close()


def get_active_inventory():
    """Fetches active targets dynamically from DB."""
    conn = get_db_connection()
    if not conn:
        return {"8.8.8.8": "Fallback Host"}

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT ip_address, label FROM ip_inventory WHERE is_active = 1")
        rows = cursor.fetchall()
        return {row["ip_address"]: row["label"] for row in rows}
    except sqlite3.Error as e:
        logging.error(f"Error fetching inventory: {e}")
        return {"8.8.8.8": "Fallback Host"}
    finally:
        conn.close()


def log_ping_result(ip, status, latency_ms):
    """Saves latency and ping status into DB with thread safety."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ping_logs (ip_address, status, latency_ms) VALUES (?, ?, ?)",
            (ip, status, latency_ms)
        )
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error logging ping result: {e}")
    finally:
        conn.close()


def archive_old_logs(days_threshold=30):
    """
    Point 14 Enhancement (Monthly Folder Archiving):
    Transfers records older than 'days_threshold' to Year/Month folder structures
    in CSV format to protect CPU/Memory performance while preserving history.
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days_threshold)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT * FROM ping_logs WHERE timestamp < ?", (cutoff_date,))
        old_records = cursor.fetchall()

        if not old_records:
            return

        # Folder Architecture: archives/2026/July/
        now = datetime.now()
        year_str = now.strftime("%Y")
        month_str = now.strftime("%B")
        target_folder = os.path.join(ARCHIVE_DIR, year_str, month_str)
        os.makedirs(target_folder, exist_ok=True)

        archive_file = os.path.join(target_folder, "network_history_archive.csv")
        file_exists = os.path.exists(archive_file)

        with open(archive_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["ID", "IP Address", "Status", "Latency (ms)", "Timestamp"])
            for row in old_records:
                writer.writerow([row["id"], row["ip_address"], row["status"], row["latency_ms"], row["timestamp"]])

        cursor.execute("DELETE FROM ping_logs WHERE timestamp < ?", (cutoff_date,))
        conn.commit()
        logging.info(f"📦 Archived {len(old_records)} records to {archive_file}")
    except Exception as e:
        logging.error(f"Archiving Failure: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
