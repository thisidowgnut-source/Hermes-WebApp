---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — Deployment & Infrastructure Guide"
document_id: "HERMES-WEBAPP-DEP-001"
version: "3.8.0"
last_updated: "2026-09-16 13:45:00 MYT"
maintainer: "GangBo Sovereign Architect"
classification: "ENGINEERING DOCS // DEPLOYMENT RUNBOOK"
lifecycle_status: "PRODUCTION / STABLE"
---

# 🚀 Deployment & Infrastructure Guide (DEPLOYMENT.md)

> **Persistent Host Automation & Service Hardening Guide.** Instructions for managing Uvicorn, Cloudflare Edge Tunnels, and FHS 3.0 directory layout via Windows Services (NSSM) and systemd.

---

## 📜 Audit & Revision Ledger

| Version | Timestamp (MYT / ISO) | Author / Agent | Scope / Root Cause | Components Updated | Validation Proof |
|:---|:---|:---|:---|:---|:---|
| **`3.8.0`** | 2026-09-16 13:45:00<br>`2026-09-16T05:45:00Z` | Antigravity Conductor | Cloudflare Quick-Start & Auto-Tunnel Architecture, WebBridge Profile 50, Health/Traces APIs, Swarm Delegation, & G:\Doh-Nut Storefront Bridge. | `docs/DEPLOYMENT.md`, `backend/routers/system.py`, `backend/routers/swarm.py`, `backend/routers/social.py` | Pytest 100% pass (275+ tests), live health & traces endpoints verified. |
| **`3.7.0`** | 2026-09-16 07:30:00<br>`2026-09-15T23:30:00Z` | Antigravity Specialist | Capability Health Probes, Restart Recovery, & Legacy Social Migration. | `backend/services/capability_probe.py`, `backend/cli/migrate_legacy_social.py` | Pytest 100% pass, dry-run zero-write verified. |
| **`3.6.0`** | 2026-09-12 16:35:00<br>`2026-09-12T08:35:00Z` | Antigravity Conductor | Pematuhan FHS 3.0 (runtime di `var/`) & pengekalan terowong PID 15260. | `docs/DEPLOYMENT.md`, `var/run/`, `var/log/` | Uvicorn 9220 & Cloudflare tunnel persistent. |
| **`3.0.0`** | 2026-07-27 18:00:00<br>`2026-07-27T10:00:00Z` | Hermes Dev Squad | Penyeliaan NSSM dan automasi skrip `cloudflare_webhook_updater.py`. | `scripts/cloudflare_webhook_updater.py` | Servis Windows auto-start lulus. |

---

## 1. The Problem
If you start the WebApp manually by running `uvicorn main:app --port 9220` in a terminal, closing that terminal will kill your remote access. If your PC restarts, you will lose connection until you log in and manually start it again.

## 2. Setting Up NSSM (Non-Sucking Service Manager)
To run both FastAPI and Cloudflare automatically on Windows startup:

### Step 1: Install NSSM
1. Download NSSM from [nssm.cc](http://nssm.cc).
2. Extract and place `nssm.exe` in `C:\Windows\System32` or your PATH.

### Step 2: Create the FastAPI Service
1. Open an Administrator PowerShell.
2. Run: `nssm install HermesWebApp`
3. In the GUI:
   - **Path:** `C:\Users\megat\AppData\Local\Programs\Python\Python311\python.exe` *(Or your specific python path)*
   - **Arguments:** `-m uvicorn main:app --host 127.0.0.1 --port 9220`
   - **Details tab -> Startup directory:** `C:\Users\megat\Hermes-WebApp`
4. Click **Install Service**.

### Step 3: Create the Cloudflare Tunnel Service
*Assuming you have a permanent Cloudflare tunnel configured (not just a quick `--url` tunnel)*:
1. Run: `cloudflared service install <YOUR-TUNNEL-TOKEN>`
2. This installs `cloudflared` as a native Windows service that will automatically start on boot and route traffic to `127.0.0.1:9220`.

### Step 4: Dynamic Webhook Updates
For dynamic setups without permanent tunnels, use `scripts/cloudflare_webhook_updater.py` to automatically fetch the `.trycloudflare.com` URL and register it with the Telegram Bot API on startup.

## 3. Service Management
You can now start, stop, or restart your web app using standard Windows Service commands without keeping a terminal open:
```powershell
Start-Service HermesWebApp
Stop-Service HermesWebApp
Restart-Service HermesWebApp
```

---

## 4. Alternatif Mudah: Stealth VBScript (Auto-Start Tanpa Servis)

Jika anda tidak mahu menggunakan NSSM, anda boleh menggunakan skrip `hermes_startup.vbs` yang disediakan di dalam repositori ini. 

---

## 5. Konfigurasi Telegram Bot Menu Button (setChatMenuButton)

Projek **Hermes-WebApp** ini direkabentuk khas untuk dipasang secara terus pada **Telegram Bot Menu Button** (butang utama di sebelah kiri ruang taipan mesej Telegram).

### Cara Pemasangan Pada Telegram:

#### Kaedah A: Menggunakan @BotFather (Manual)
1. Buka Telegram dan cari **[@BotFather](https://t.me/BotFather)**.
2. Hantar arahan `/setmenubutton`.
3. Pilih bot anda dari senarai.
4. Masukkan pautan URL Cloudflare WebApp anda (contoh: `https://xxxx.trycloudflare.com`).
5. Masukkan nama teks butang (contoh: `🦅 Open Hermes OS`).

#### Kaedah B: Pengemaskinian Automatik (Skrip Python)
Jalankan skrip `scripts/cloudflare_webhook_updater.py` yang akan secara automatik mendaftarkan `setChatMenuButton` dengan pautan `trycloudflare.com` terkini:
```python
import requests
token = "BOT_TOKEN_ANDA"
web_app_url = "https://xxxx.trycloudflare.com"

requests.post(f"https://api.telegram.org/bot{token}/setChatMenuButton", json={
    "menu_button": {
        "type": "web_app",
        "text": "🦅 Open Hermes OS",
        "web_app": {"url": web_app_url}
    }
})
```


> **AMARAN PENTING:** 
> Jika anda menggunakan mod ini dengan *Cloudflare Quick Tunnel* biasa, URL anda akan **bertukar** setiap kali PC *restart*. Ini bermakna anda perlu mengemaskini semula URL di dalam Bot Telegram (`@BotFather`). Untuk penyelesaian kekal, anda MESTI mendaftar akaun Cloudflare dan pasang Named Tunnel seperti di Langkah 2 di atas.

Your Hermes OS WebApp is now a persistent, silent background command center!

---

## 6. Honest Capability Health & Restart Recovery

Hermes WebApp features built-in honest capability probing to verify that required executables, databases, and network adapters are genuinely operational (avoiding false "ONLINE" assertions based on file presence alone):

- **AGY CLI Probe**: Empirically executes `agy --version` with subprocess timeouts.
- **Hermes Coordinator**: Reads feature flag `HERMES_ADAPTER_ENABLED` and checks coordinator protocol readiness.
- **Database Probe**: Runs `SELECT 1` and inspects `PRAGMA journal_mode` (WAL mode enforcement).
- **WebBridge Probe**: Probes `http://127.0.0.1:10087/health` for local automation health.
- **Tunnel Probe**: Inspects local `cloudflared` process presence and binary readiness.

During application startup, `MissionService.reconcile_startup()` identifies any uncompleted running runs that crashed across restarts and marks them `INTERRUPTED` while appending recovery audit events to `missions.db`.

---

## 7. Legacy Social Autopilot Data Migration

To migrate existing SQLite drafts (`social_autopilot.db`) or JSON draft exports into the new durable ledger (`missions.db`):

```powershell
# 1. Perform a dry-run (writes 0 rows, verifies SHA-256 integrity):
python -m backend.cli.migrate_legacy_social --source var/lib/social_autopilot.db --destination var/lib/missions.db

# 2. Perform live migration with manifest logging:
python -m backend.cli.migrate_legacy_social --source var/lib/social_autopilot.db --destination var/lib/missions.db --live
```

---

## 8. Cloudflare Quick-Start & `G:\Doh-Nut` Storefront Bridge Architecture

### 8.1 Zero-Cloud 1-Command Startup
Hermes OS runs 100% sovereignly without requiring Docker, Redis, or cloud databases.

```powershell
# Terminal 1: Launch FastAPI Backend (Port 9220)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 9220

# Terminal 2: Expose via Cloudflare Quick Tunnel (Zero Port-Forwarding)
cloudflared tunnel --url http://127.0.0.1:9220
```

### 8.2 Live Observability & Comprehensive Health Probing
The system exposes instant health checks and execution trace streams:
- **Comprehensive Health Check**: `GET /api/health/comprehensive`
  - Validates system load (CPU, RAM, Disk), SQLite Durable Queue backlog, SQLite Social DB connectivity, active Swarm agent counts, and GangNiaga WebBridge connectivity (port 10087).
- **Execution Traces Export**: `GET /api/traces?limit=50`
  - Aggregates recent durable scheduled jobs, swarm agent execution logs, and mission events into a single unified trace stream.

### 8.3 Multi-Agent Swarm Delegation (`goal_mode`)
- **Endpoint**: `POST /api/swarm/delegate`
- Spawns an orchestrator lead (`role="orchestrator"`) with concurrent subagent workers (`role="researcher"`, `role="engineer"`, etc.) linked to a persistent `delegation_id` (`del-xxxx`), queryable via `GET /api/swarm/delegations`.

### 8.4 Connecting with `G:\Doh-Nut` Storefront (Dual-Mode Architecture)
The Doh-Nut Next.js 16 App Router storefront (`G:\Doh-Nut`) connects with Hermes-WebApp in three seamless modes:

1. **Production Vercel Bridge (Default / Fail-Soft)**:
   - Configured via `DOHNUT_API_URL="https://dowgnut-custom.vercel.app"`.
   - Hermes queries `/api/donuts` and `/api/admin/stats` automatically with a 30s TTL cache (`backend/services/dohnut_link.py`).
2. **Local Dual-Mode Development Bridge**:
   - Start the local Doh-Nut dev server in `G:\Doh-Nut`:
     ```powershell
     cd G:\Doh-Nut
     bun dev # Runs on http://127.0.0.1:3000
     ```
   - In `Hermes-WebApp\.env`, override:
     ```env
     DOHNUT_API_URL="http://127.0.0.1:3000"
     ```
   - Hermes will seamlessly fetch catalog items, stock counters, and order queues from your local Next.js dev server.
3. **Direct SQLite Prisma Shared Database Mode**:
   - `G:\Doh-Nut` stores data in SQLite at `G:\Doh-Nut\prisma\dev.db` or `G:\Doh-Nut\db\custom.db`.
   - Hermes backend can directly query/inspect the Prisma SQLite database without HTTP network latency.
4. **WebBridge Chrome Profile 50 Publishing**:
   - `POST /api/dohnut/social/publish-webbridge` synchronizes draft scripts to the OS clipboard via `clip.exe` and navigates authenticated Chrome Profile 50 tabs directly to TikTok, Instagram, Threads, Facebook, X, and YouTube.


