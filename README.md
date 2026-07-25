# 📡 Dawit Telecom Enterprise Network Health & Automated Self-Healing Suite

A robust, multi-threaded enterprise network health monitoring and incident response suite. Built with Python, it continuously audits node latency, dispatches instant notifications via Telegram, offers interactive REST/Web UI dashboards, and executes SSH recovery routines under node failures.

---

## 📐 System Architecture & Flowchart

```mermaid
flowchart TD
    A["Ping Scan Scheduler<br/>(Parallel Threads)"] --> B["IPv4 ICMP Target Check"]
    
    B --> C["Host ONLINE"]
    B --> D["Host OFFLINE"]
    
    C --> E["Record Latency into SQLite"]
    D --> F["Trigger Threshold Audit"]
    
    F -->|Failures >= 3| G["🚨 Send Telegram Alert<br/>⚡ Execute SSH Healing"]
    
    E --> H["Update Flask Web Dashboard<br/>(http://localhost:5000)"]



