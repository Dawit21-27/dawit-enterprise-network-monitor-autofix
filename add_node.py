import sqlite3
import sys

def inject_new_ip(ip_address, label):
    """Securely inserts a new network node into the database inventory at runtime."""
    try:
        conn = sqlite3.connect("network_monitor.db")
        cursor = conn.cursor()
        
        # አዲሱን አይፒ ወደ መዝገቡ (Inventory) ያስገባል
        cursor.execute("""
            INSERT OR IGNORE INTO ip_inventory (ip_address, label, is_active)
            VALUES (?, ?, 1)
        """, (ip_address.strip(), label.strip()))
        
        conn.commit()
        print(f"🎯 Success: New node [{ip_address}] ({label}) has been added to the network inventory!")
        
    except sqlite3.Error as e:
        print(f"❌ Database Error: Failed to inject node. Details: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🖥️ --- Dawit Enterprise Inventory Injector ---")
    
    # ተጠቃሚው የሚጨምረውን አይፒ ይጠይቃል
    user_ip = input("Enter New IP Address to Monitor (e.g., 2.2.2.2): ")
    user_label = input("Enter Site Name / Label (e.g., Insa-Backup-Switch): ")
    
    if user_ip and user_label:
        inject_new_ip(user_ip, user_label)
    else:
        print("❌ Error: IP Address and Label cannot be empty.")
