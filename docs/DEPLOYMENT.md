---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — Deployment & Infrastructure Guide"
document_id: "HERMES-WEBAPP-DEP-001"
version: "3.6.0"
last_updated: "2026-09-12 16:35:00 MYT"
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
