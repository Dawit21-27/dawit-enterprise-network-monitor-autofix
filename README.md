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

```
---
## 📸 System Previews

### 1. Visual Web Dashboard (`http://localhost:5000`)
Real-time node telemetry dashboard status rendering:

## 📸 System Previews

### 1. Visual Web Dashboard (`http://localhost:5000`)
Real-time node telemetry dashboard status rendering:

```mermaid
flowchart TD
    subgraph Dashboard["📊 DAWIT TELECOM - NETWORK HEALTH DASHBOARD"]
        direction TB
        N1["🖥️ Node: 192.168.1.1 <br/> ⏱️ Latency: 12.4 ms <br/> 🟢 Status: ONLINE"]
        N2["🌐 Node: 8.8.8.8 (Google DNS) <br/> ⏱️ Latency: 42.1 ms <br/> 🟢 Status: ONLINE"]
        N3["⚠️ Node: 10.0.0.12 (Server) <br/> ⏱️ Latency: --- <br/> 🔴 Status: OFFLINE"]
    end

    style Dashboard fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
    style N1 fill:#166534,stroke:#4ade80,stroke-width:1px,color:#fff
    style N2 fill:#166534,stroke:#4ade80,stroke-width:1px,color:#fff
    style N3 fill:#991b1b,stroke:#f87171,stroke-width:1px,color:#fff
```

### 2. Interactive Telegram Bot & Critical Incident Alerts
Instant outage notifications with inline controls for status queries.

```mermaid
flowchart TD
    subgraph Bot["🤖 TELEGRAM INCIDENT BOT"]
        direction TB
        Alert["🚨 CRITICAL ALERT: HOST DOWN<br/>━━━━━━━━━━━━━━━━━━━━━<br/>🎯 Target IP: 10.0.0.12<br/>⚠️ Drop Count: 3/3 Consecutive ICMP Drops<br/>⚡ Recovery: SSH Self-Healing Triggered"]
        
        subgraph Buttons["Interactive Actions"]
            B1["📊 Live Status"] --- B2["🔄 Re-Check Node"]
        end
    end

    style Bot fill:#0f172a,stroke:#818cf8,stroke-width:2px,color:#fff
    style Alert fill:#1e1b4b,stroke:#a78bfa,stroke-width:1px,color:#fff
    style Buttons fill:#312e81,stroke:#6366f1,color:#fff

```


### 3. Engine Telemetry Logs
Asynchronous multi-threaded execution traces showing ping scanning and dynamic fallback handling.

```mermaid

flowchart TD
    subgraph Engine["⚙️ TERMINAL ENGINE LOGS (Multi-Threaded)"]
        direction TB
        L1["[INFO] Ping scan initiated for subnet 192.168.1.0/24..."] --> L2
        L2["[SUCCESS] 192.168.1.1 is ONLINE (12.4ms) ➔ SQLite Updated"] --> L3
        L3["[WARNING] Target 10.0.0.12 failed ICMP response! (Attempt 1/3)"] --> L4
        L4["[CRITICAL] Target 10.0.0.12 Threshold Exceeded! (Attempt 3/3)"] --> L5
        L5["[ACTION] Dispatching Telegram Alert ➔ Executing SSH Healing..."]
    end

    style Engine fill:#020617,stroke:#06b6d4,stroke-width:2px,color:#fff
    style L1 fill:#0f172a,stroke:#334155,color:#38bdf8
    style L2 fill:#052e16,stroke:#16a34a,color:#4ade80
    style L3 fill:#451a03,stroke:#d97706,color:#fbbf24
    style L4 fill:#450a0a,stroke:#dc2626,color:#f87171
    style L5 fill:#2e1065,stroke:#9333ea,color:#c084fc

 ```
---

## 👥 User Guide (በተግባር እንዴት እንደሚሰራ)

1. **Passive Monitoring (Visual Dashboard):**
   * Open any browser and navigate to `http://localhost:5000`.
   * Monitor round-trip latency (RTT in ms) and online/offline statuses updated automatically every 10 seconds.

2. **Active Bot Monitoring:**
   * Open Telegram and query the bot.
   * Send `/status` or tap **`📊 Live Status`** for instantaneous host status reports.
   * Send `/check <IP_ADDRESS>` (e.g., `/check 8.8.8.8`) to run on-demand security-sanitized diagnostic checks.

3. **Incident Remediation:**
   * Upon detecting 3 consecutive ICMP host failures, the system executes SSH self-healing routines to restart failing services and alerts the engineer.

---

## 🛠️ Installation & Setup Guide

```bash
# 1. Clone Repository
git clone [https://github.com/YOUR_GITHUB_USERNAME/dawit-enterprise-network-monitor-autofix.git](https://github.com/YOUR_GITHUB_USERNAME/dawit-enterprise-network-monitor-autofix.git)
cd dawit-enterprise-network-monitor-autofix

# 2. Install Required Dependencies
pip install flask python-dotenv requests

# 3. Create .env file with your credentials


---

## ⚖️ System Evaluation: Strengths & Limitations

### 🟢 Core Strengths (የሲስተሙ ጠንካራ ጎኖች)
* **High-Performance Concurrency:** Uses asynchronous multi-threading to continuously monitor multiple IP nodes in parallel without execution blocking or latency buildup.
* **Full PC Cross-Platform Native Support:** Runs at 100% native capacity on desktop environments (Windows, Linux, macOS) with full ICMP, SSH (`paramiko`), and SMS gateway support.
* **Resilient Architecture & Graceful Degradation:** Built-in fallback mechanisms ensure system continuity; when restricted on mobile OS environments (Pydroid 3), it smoothly transitions into simulation mode without process crashes.
* **Enterprise Security Measures:** Strict input sanitization via Python's `ipaddress` module prevents command injection vulnerabilities on dynamic user inputs (`/check <IP>`).
* **Automated Data Lifecycle Management:** Dynamic log rotation archives telemetry history into monthly CSV structures, preventing SQLite database bloat over extended operation periods.
* **Multi-Interface Accessibility:** Offers dual-view monitoring—a dynamic Flask Web Analytics Dashboard for browsers and an event-driven Telegram Bot for mobile engineers.

---

### 🟡 Environment-Specific Limitations (የአካባቢ ውስንነቶች)
> **Note:** The core system code is fully functional for Enterprise PC/Server deployment. The following are mobile-runtime constraints only:

* **Mobile OS Compilation Constraints:** When deployed on mobile platforms (Android/Pydroid 3), C-compiled dependencies (like `cryptography/paramiko` for native SSH) require cross-compilation binaries, triggering the system's dynamic simulation fallback.
* **Single-Node Deployment:** The current engine operates as a centralized monitor; network partitions between the monitor and targets could trigger false-positive outage alerts.
* **Basic Authentication on Web UI:** The Flask web dashboard currently runs without localized HTTP Basic Auth or OAuth2 middleware, suitable for internal LANs or private VPNs.

---

## 🚀 Future Enhancements & Roadmap (ወደፊት የሚሻሻሉ ነገሮች)

1. **Distributed Agent Nodes:** Transitioning from a single centralized scanner to a distributed worker architecture (using Celery / Redis) for multi-region host auditing.
2. **Advanced Security Integration:** Implementing OAuth2 / JWT authentication layers for the Flask visual dashboard to support multi-tenant role-based access.
3. **Enhanced Visual Analytics:** Integrating `Chart.js` or `Grafana` connectors to display real-time latency graphs and historical uptime percentage metrics.
4. **Automated SMS & PagerDuty Integration:** Adding native PagerDuty API integrations alongside Twilio for enterprise-level escalation chains.


