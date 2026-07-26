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
    """Initializes the enterprise database schema and seeds inventory from environment variables."""
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

        # Dynamic Engine: Loading target nodes securely from the .env configuration
        env_ips = os.getenv("TARGET_HOSTS", "8.8.8.8,1.1.1.1")
        ip_list = [ip.strip() for ip in env_ips.split(",") if ip.strip()]

        for ip in ip_list:
            cursor.execute("""
                INSERT OR IGNORE INTO ip_inventory (ip_address, label) 
                VALUES (?, ?)
            """, (ip, f"Node-{ip}"))

        conn.commit()
        logging.info("Database initialized successfully from environment config.")
        
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
    Safely archives old ping logs into dynamic chronological folders (YEAR/MONTH/WEEK)
    based on the ACTUAL data timestamp, preventing data misplacement and resource locking.
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
      
        cutoff_date = (datetime.now() - timedelta(days=days_threshold)).strftime("%Y-%m-%d %H:%M:%S")

        # 1. Fetch old records from the database
        cursor.execute("SELECT * FROM ping_logs WHERE timestamp < ? ORDER BY timestamp ASC", (cutoff_date,))
        old_records = cursor.fetchall()

        if old_records:
            # Group records by their actual year, month, and week to prevent folder mixing
            for row in old_records:
                
                record_time = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
                
                year_str = record_time.strftime("%Y")
                month_str = record_time.strftime("%B")

                
                record_day = record_time.day
                week_of_month = (record_day - 1) // 7 + 1
                if week_of_month == 1: suffix = "1st_Week"
                elif week_of_month == 2: suffix = "2nd_Week"
                elif week_of_month == 3: suffix = "3rd_Week"
                else: suffix = "4th_Week"

                target_folder = os.path.join(ARCHIVE_DIR, year_str, month_str, suffix)
                os.makedirs(target_folder, exist_ok=True)
                archive_file = os.path.join(target_folder, "network_history_archive.csv")

                # Write to CSV securely
                file_exists = os.path.exists(archive_file) and os.path.getsize(archive_file) > 0
                with open(archive_file, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["ID", "IP Address", "Status", "Latency (ms)", "Timestamp"])
                    
                    writer.writerow([row["id"], row["ip_address"], row["status"], row["latency_ms"], row["timestamp"]])

            cursor.execute("DELETE FROM ping_logs WHERE timestamp < ?", (cutoff_date,))
            conn.commit()
            logging.info(f"Successfully segregated and archived {len(old_records)} records sequentially.")
            
    except Exception as e:
        logging.error(f"Archiving Strategy Failure: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
