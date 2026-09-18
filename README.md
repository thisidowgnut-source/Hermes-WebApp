---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — System Architecture & Operating Guide"
document_id: "HERMES-WEBAPP-DOC-001"
version: "3.9.0"
last_updated: "2026-09-16 14:35:00 MYT"
maintainer: "GangBo Sovereign Architect"
classification: "MISSION-CRITICAL // SOVEREIGN ENGINE"
lifecycle_status: "PRODUCTION / STABLE"
---

# 🎼 Hermes OS & Doh-Nut Sovereign Mission Control

> **Ultra-low latency Telegram Mini App & Progressive Web App (PWA) providing unstoppable remote PC orchestration, live browser automation, multi-agent telemetry, and All-in-1 mission control for Doh-Nut (`thisisdohnut@gmail.com`).**

---

## 📜 Audit & Revision Ledger

| Version | Timestamp (MYT / ISO) | Author / Agent | Root Cause / Rationale | Code Scope & Components Touched | Empirical Validation Proof |
|:---|:---|:---|:---|:---|:---|
| **`3.9.0`** | 2026-09-16 14:35:00<br>`2026-09-16T06:35:00Z` | Antigravity Conductor | Agent-Reach Internet Capability Router: 15-Platform Ingestion, yt-dlp Subtitle Extraction, Jina Reader Zero-Headless Web Ingestion & Bento HUD 1-Tap Bar. | `backend/services/reach_engine.py`, `backend/routers/reach.py`, `static/index.html`, `docs/`, `README.md` | 292/292 Pytest suite passed (100% green, 36 test files). |
| **`3.8.0`** | 2026-09-16 13:45:00<br>`2026-09-16T05:45:00Z` | Antigravity Conductor | Swarm Goal Mode Delegation, Comprehensive Health & Traces APIs, SocialValidator Auto-trimming & SMS-v1.0 Approval Audit Log. | `backend/routers/social.py`, `backend/routers/dohnut.py`, `backend/routers/swarm.py`, `backend/routers/system.py`, `docs/`, `README.md` | 275+ Pytest suite passed (100% green), Zero-Cloud RM0 architecture verified. |
| **`3.6.0`** | 2026-09-12 16:35:00<br>`2026-09-12T08:35:00Z` | Antigravity Conductor | Penstrukturan FHS 3.0 (Direktori PRO), Penghapusan Jitter Butang (Emil Kowalski Craft), dan Arkitektur Mobile-First Sifar-Bertindih. | `static/index.html`, `var/`, `tools/mcp/`, `docs/`, `tests/test_dohnut_api.py`, `README.md` | FHS 3.0 root 13 fail, 0 jitter butang pada hover, 0 bertindih pada viewport 390x844 & 360x740, 5/5 Doh-Nut tests passing. |
| **`3.5.0`** | 2026-09-12 15:15:00<br>`2026-09-12T07:15:00Z` | Antigravity Conductor | Penyatuan All-in-1 Mission Control Doh-Nut ke dalam Hermes-WebApp tanpa mengganggu persediaan Telegram Menu Button. | `backend/routers/dohnut.py`, `backend/main.py`, `static/index.html`, `README.md` | 5/5 API Endpoints 200 OK, Chrome DevTools MCP Desktop & Mobile (390px) verified, Zero console errors. |
| **`3.4.0`** | 2026-09-12 02:30:00<br>`2026-09-11T18:30:00Z` | Conductor Agent | Pengesahan profil media sosial Chrome Profile 50 (`thisisdohnut@gmail.com`) dan integrasi WebBridge port 10087. | `static/index.html`, `scripts/ai_labs_dispatcher.py` | 6 platform disahkan, 62/62 Bun tests pass. |
| **`3.0.0`** | 2026-07-27 18:00:00<br>`2026-07-27T10:00:00Z` | Hermes Dev Squad | Reka bentuk semula Bento-Box Dashboard, pembetulan CSS overlay z-index, integrasi Termux Hacker's Keyboard. | `static/index.html`, `backend/websockets/terminal.py` | 84/84 Pytest suite passed, 14 modul UI lulus ujian headless DOM. |

---

## 🎯 Mission & Core Mandate

**Hermes OS** menggabungkan kuasa pengkomputeran desktop penuh bersama kemudahan capaian mudah alih Telegram. Sistem ini membebaskan pengendali daripada kekangan bot Telegram biasa — membolehkan akses shell PowerShell sebenar, pelayaran web berkamera (Chromium frame streaming), pemantauan skuad AI pelbagai ejen, dan pemantauan perniagaan secara masa-nyata dari mana-mana peranti di seluruh dunia.

Dengan penyepaduan **Doh-Nut Sovereign HQ**, Hermes-WebApp kini berfungsi sebagai pusat kawalan sehenti (All-in-1 Mission Control) yang mengawal:
1. **Operasi Dapur & Jualan Live**: Hasil jualan harian (RM 1,420.50), penjejakan pesanan 4 peringkat (Baking Kanban), barisan katering 150 pax, dan stok donut signatur.
2. **Social Autopilot 6-Platform**: Penjanaan promosi pintar dan penyiaran 1-ketuk terus ke TikTok, Instagram, Threads, Facebook, X, dan YouTube melalui Chrome Profile 50 & GangNiaga WebBridge.
3. **Telemetri Skuad Ejen (Swarm)**: Pemantauan langsung Hermes Conductor, Antigravity Conductor, GangNiaga WebBridge, dan Open Design Daemon.
4. **10 Enjin Google AI Labs**: Pelancar pantas untuk Mixboard, Google Stitch, Play with Putty, Google Jules, Google Opal, Google AI Studio, Gemini NotebookLM, Google Flow, ChatGPT Plus, dan Labs Hub.

---

## 🏗️ Architectural Topology

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       CLIENT VIEWPORT / ACCESS INTERFACES                                 │
│  ┌──────────────────────────────────────────────────┐  ┌───────────────────────────────────────────────┐  │
│  │   TELEGRAM MINI APP (Mobile Viewport 390x844px)  │  │        DESKTOP OLED PWA (Port 9220)           │  │
│  │   • Launch via Telegram Chat Menu Button         │  │        • Standalone Progressive Web App       │  │
│  │   • WebApp SDK (Haptic, Viewport Height Sync)    │  │        • Full-width 16-Module Bento-Box       │  │
│  └─────────────────────────┬────────────────────────┘  └───────────────────────┬───────────────────────┘  │
└────────────────────────────┼───────────────────────────────────────────────────┼──────────────────────────┘
                             │                                                   │
                             ▼                                                   ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               CLOUDFLARE SECURE EDGE TUNNEL (HTTPS / WSS)                                 │
│  • cloudflared tunnel --url http://127.0.0.1:9220 (Persistent Background PID 15260)                      │
│  • Automasi Dynamic URL: scripts/cloudflare_webhook_updater.py -> Telegram API setChatMenuButton          │
│  • Zero-Disruption Failover: Pelayan lokal boleh di-reload tanpa memutuskan URL awam Telegram             │
└────────────────────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                             │
                                                             ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FASTAPI ASYNC BACKEND (Host OS: Port 9220)                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                          CORE REST ROUTERS                                          │  │
│  │  • /api/stats (CPU, RAM, Disk)             • /api/dohnut/stats (Baking & Store Ops)                 │  │
│  │  • /api/files (Secure Workspace Explorer)  • /api/dohnut/social/generate (6-Platform Campaigns)     │  │
│  │  • /api/macro/* (Clean Temp, Kill Zombies) • /api/dohnut/social/publish-webbridge (Profile 50 Post) │  │
│  │  • /api/swarm/* (Agent Telemetry & Spawn)  • /api/dohnut/agent-swarm/status (4-Node Swarm)          │  │
│  │  • /api/audio/* (VAD & Voice CLI)          • /api/dohnut/ai-labs/* (10 AI Labs Dispatcher)          │  │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                      FULL-DUPLEX WEBSOCKET HUBS                                     │  │
│  │  • /ws/terminal ──► ConPTY / WinPTY (PowerShell 7 ANSI Streaming with Termux Key Matrix)             │  │
│  │  • /ws/browser  ──► Playwright Chromium (JPEG / WebP Frame Streaming with Click & Type Events)     │  │
│  │  • /ws/swarm    ──► Multi-Agent JSON Heartbeat & Live Log Aggregator                                │  │
│  │  • /ws/audio    ──► PCM Audio Stream + VAD + Real-Time Whisper Transcription                        │  │
│  │  • /ws/hitl     ──► Human-in-the-Loop Interventions (Authorization & Bypass Prompts)                │  │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                             │
                                                             ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               HOST ENVIRONMENT, HARDWARE & EXTERNAL DAEMONS                               │
│  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────┐  │
│  │  Windows 11 Host OS    │  │ GangNiaga WebBridge    │  │ Open Design Daemon     │  │ Chrome User    │  │
│  │  • PowerShell 7 (pwsh) │  │  • Port 10087 (Live)   │  │  • Port 7456 (Live)    │  │   Profile 50   │  │
│  │  • Python 3.11 venv    │  │  • DOM Injection Hook  │  │  • Neo-Brutalism Engine│  │  • TikTok, IG, │  │
│  │  • Task Scheduler      │  │  • Chrome CDP Link     │  │  • 152 Design Tokens   │  │    X, FB, YT   │  │
│  └────────────────────────┘  └────────────────────────┘  └────────────────────────┘  └────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎛️ Complete Catalog of 16 Sovereign Modules

| # | Module ID | Label & Icon | Description | Keyboard / Touch Features |
|:---:|:---|:---|:---|:---|
| **1** | `dohnut` | 🍩 **Doh-Nut Sovereign HQ** | Pusat kawalan All-in-1 jualan donut, pesanan live, promosi viral, telemetri swarm, dan 10 makmal AI. | 4 Tab Beralih, KPI kewangan, Butang 1-ketuk WebBridge. |
| **2** | `terminal` | 🖥️ **Remote Terminal** | Sesi penuh PowerShell (`pwsh.exe`) dipancarkan melalui xterm.js dengan penapisan PTY ping bersih. | Baris Kekunci Termux Hacker (`ESC`, `TAB`, `CTRL+C`, `|`, `~`, `/`). |
| **3** | `browser` | 🌐 **Hermes Vision** | Pelayar Chromium Playwright kawalan jauh dengan penstriman bingkai masa-nyata. | Pilihan URL 1-ketuk (Google, GitHub, Hermes, Ollama), kawalan sentuh. |
| **4** | `swarm` | 🤖 **Multi-Agent Swarm** | Pemantau status ejen AI (Hermes, Antigravity, WebBridge, Open Design) berserta penggunaan memori/CPU. | Butang Spawn pantas, penapis log langsung. |
| **5** | `kanban` | 📋 **Kanban Tasks** | Papan pengurusan tugasan berperingkat (To Do, In Progress, Review, Completed). | Seret-dan-lepas (*drag & drop*), tambah kad pantas. |
| **6** | `files` | 📁 **File Explorer** | Penjelajah fail sistem dengan fungsi muat turun, baca (≤2MB), dan edit secara selamat. | Navigasi direktori pantas, pratonton teks. |
| **7** | `editor` | 📝 **Code Editor** | Penyunting kod dalam talian berasaskan monokrom OLED dengan penyerlah sintaks (*syntax highlighting*). | Simpan terus ke fail hos, sokongan format pelbagai bahasa. |
| **8** | `audio` | 🎤 **Voice & STEM Audio** | Enjin kawalan suara berasaskan Voice Activity Detection (VAD) dan pengasingan audio STEM. | Pengenalan arahan suara hands-free, visualizer gelombang. |
| **9** | `netscan` | 📡 **Network Scanner** | Pengimbas sambungan rangkaian tempatan, port terbuka, dan status perkakasan IoT. | Peta topologi IP, pengesanan peranti asing. |
| **10** | `threat` | 🛡️ **Threat Sentinel** | Pengesan proses mencurigakan, pemantau integriti fail (FIM), dan penguatkuasa firewall. | Log amaran keselamatan merah/kuning, bunuh proses 1-ketuk. |
| **11** | `services` | ⚙️ **Services Manager** | Pengurus servis sistem latar belakang Windows & Linux (Start, Stop, Restart). | Pantau status servis kritikal (Ollama, WebBridge, Uvicorn). |
| **12** | `forensics` | 🔬 **Forensics Suite** | Audit mendalam log keselamatan Windows (Event Viewer) dan jejak audit PowerShell. | Carian teks log, analisis ancaman MITRE ATT&CK. |
| **13** | `workflow` | 🔁 **Workflow Engine** | Penjadual tugas berulang (Cron Jobs & DAGs) dengan pengesahan persistence. | Integrasi terus dengan Windows Task Scheduler. |
| **14** | `obsgraph` | 🕸️ **Obsidian Knowledge Graph** | Peta interaktif 2,700+ nota Obsidian Vault dengan sokongan carian pantas MOC. | Visualisasi nod bercahaya, penjelajah wikilink. |
| **15** | `social` | 📢 **Social Media Publisher** | Penyiaran mesej promosi am merentasi platform media sosial. | Pratonton draf, suis kelulusan HITL. |
| **16** | `appdrawer` | 🎛️ **Sub-Systems Drawer** | Katalog pelancar menyeluruh bagi semua 16 subsistem dalam satu paparan grid modular. | Carian pantas nama modul, susun atur responsif. |

---

## 🍩 Doh-Nut Sovereign HQ: Deep Feature Breakdown

Modul `#mod-dohnut` dibangunkan khusus bagi menyokong ekosistem perniagaan **Doh-Nut** (`thisisdohnut@gmail.com`). Modul ini merangkumi 4 sektor utama:

### 1. Store & Baking Operations Tab
- **Financial KPIs**:
  - *Today's Revenue*: RM 1,420.50 (34 pesanan diselesaikan melalui Billplz & Kiosk).
  - *Active Baking Orders*: 8 pesanan dalam saluran pemprosesan.
  - *Catering Line*: 150 Pax ditempah (Syarikat Maju Tech + Event Bangi Gateway).
  - *Dough Batches*: 14 baki adunan sedia digoreng ("Good Vibe. Good Doh.").
- **4-Stage Baking & Glazing Kanban**:
  1. *Preparing (4)*: Uli dan peram doh (#408 - 2x Box of 6).
  2. *Deep Frying (2)*: Goreng keemasan pada suhu 175°C (#405 - 1x Kuih Burger).
  3. *Glazing (1)*: Salutan Frosting Pink & taburan manik gula (#401).
  4. *Ready / Dispatch (1)*: Pembungkusan kotak eco sedia untuk Lalamove (#399).
- **Inventori Perisa Signatur**:
  - 🍔 *Kuih Burger Malaysia*: 42 baki
  - 🍠 *Sira Kuih Keria*: 38 baki
  - 🌶️ *Sira Sambal Pedas Manis*: 25 baki
  - ✨ *Classic Glazed Vanilla*: 50 baki
  - 🍵 *Matcha White Choco*: 8 baki (**LOW STOCK**)

### 2. Social Autopilot Tab (Chrome Profile 50 Linked)
- **Omnichannel Viral Generator**:
  - Pengendali hanya perlu memasukkan 1 topik promosi (contoh: *"Combo Donut Kuih Burger Viral RM15!"*).
  - Sistem menjana pakej lengkap 6 platform serentak dalam masa nyata:
    * **TikTok (`@thisisdohnut`)**: Skrip video 9:16, arahan visual pembukaan 1.5s (*pattern interrupt*), audio voiceover, dan tanda pagar viral.
    * **Instagram Reels**: Teks kapsyen menarik, tawaran diskaun pagi, seruan tindakan (*Call to Action*).
    * **Threads**: Format soalan debat santai bagi merangsang komen dan interaksi pengguna.
    * **Facebook**: Salinan teks mesra korporat mempromosikan pakej katering pejabat (30 hingga 500 pax).
    * **X (Twitter)**: Tweet ringkas, padat, dan pautan terus ke portal pembelian.
    * **YouTube Shorts**: Format skrip video pendek berasaskan ASMR dapur gorengan.
- **1-Tap Post via GangNiaga WebBridge**:
  - Menekan butang `1-TAP POST` menghantar permintaan ke endpoint `/api/dohnut/social/publish-webbridge`.
  - Pelayan berkomunikasi dengan WebBridge (`http://127.0.0.1:10087`) untuk memfokuskan tab aktif pada Chrome Profile 50 dan menyuntik teks secara automatik tanpa perlu log masuk semula.

### 3. Agent Swarm Tab
- Memaparkan status langsung 4 nod pengkomputeran pintar:
  - 🟢 **Hermes Conductor (v0.19.0)**: Pengendali OS 24/7 & Telegram Watchdog.
  - 🟢 **Antigravity Conductor (v1.2.2)**: Enjin pembangun full-stack & jambatan ACP.
  - 🟢 **GangNiaga WebBridge (v3.0)**: Pengawal pelayar Chrome Profile 50.
  - 🟢 **Open Design Generative UI Daemon (Port 7456)**: Pelayan 152 sistem reka bentuk UI.
- **Butang Tindakan Pantas**:
  - `RUN BUN 62/62`: Menjalankan suite ujian regresi kod `G:\Doh-Nut`.
  - `SYNC VAULT`: Menyelaraskan rujukan MOC dan pautan graf Obsidian.
  - `KILL ZOMBIE PORTS`: Membersihkan proses terbiar yang memegang port sistem.

### 4. 10 Google AI Labs & Autonomous Coding Engines Tab
Menyediakan pelancar terus 1-ketuk bagi memfokuskan dan membuka makmal AI pilihan pada Chrome Profile 50:
1. **Mixboard**: Penjanaan jingle kempen & kesan bunyi ASMR.
2. **Google Stitch**: Penjana antaramuka UI generatif dan token reka bentuk `DESIGN.md`.
3. **Play with Putty**: Persekitaran vibe-coding pantas.
4. **Google Jules**: Pengaturcara PR GitHub berautonomi penuh.
5. **Google Opal**: Eksperimen visual dan pembinaan prototaip aplikasi pantas.
6. **Google AI Studio**: Akses percuma model Gemini 2.0 Flash / Pro.
7. **Gemini NotebookLM**: Sintesis dokumen dan penjanaan podcast perbincangan.
8. **Google Flow**: Automasi alur kerja berasaskan nod visual.
9. **ChatGPT Plus (Canvas/Voice)**: Rundingan arkitektur peringkat tinggi.
10. **Google Labs Hub**: Hab utama pendedahan model eksperimen Google.

---

## 📡 Comprehensive API Reference

### 1. Doh-Nut Sovereign Mission Control Endpoints

| Kaedah | Laluan Endpoint | Penerangan & Skop | Parameter / Format Input | Contoh Respons / Output |
|:---:|:---|:---|:---|:---|
| `GET` | `/api/dohnut/stats` | Mengambil data operasi jualan, saluran pembakar, barisan katering, dan inventori donut. | Tiada | `{"ok": true, "store_name": "DOH-NUT HQ", "revenue_today": 1420.50, "active_orders": 8, ...}` |
| `GET` | `/api/dohnut/social/accounts` | Mengambil senarai akaun media sosial rasmi yang disahkan aktif pada Chrome Profile 50. | Tiada | `{"ok": true, "brand": "DOH-NUT", "accounts": [{"platform": "TikTok", "handle": "@thisisdohnut", ...}]}` |
| `POST` | `/api/dohnut/social/generate` | Menjana draf kempen promosi serentak untuk 6 platform media sosial utama. | `{"topic": "Promo Combo", "tone": "viral hype"}` | `{"ok": true, "topic": "...", "package": {"tiktok": "...", "instagram": "...", ...}}` |
| `POST` | `/api/dohnut/social/publish-webbridge` | Memajukan draf teks ke GangNiaga WebBridge (port 10087) untuk disiarkan pada Profile 50. | `{"platform": "tiktok", "content": "Teks post..."}` | `{"ok": true, "message": "Dispatched to WebBridge", "platform": "tiktok"}` |
| `GET` | `/api/dohnut/ai-labs/status` | Memeriksa ketersediaan pelayan WebBridge dan daemon Open Design. | Tiada | `{"webbridge": {"online": true, "port": 10087}, "open_design": {"online": true, "port": 7456}}` |
| `POST` | `/api/dohnut/ai-labs/focus` | Memfokuskan tetingkap pelayar ke salah satu daripada 10 makmal AI terpilih. | `{"lab_id": "stitch"}` | `{"ok": true, "focused_lab": "Google Stitch"}` |
| `GET` | `/api/dohnut/agent-swarm/status` | Mengambil telemetri status bagi Hermes, Antigravity, WebBridge, dan Open Design. | Tiada | `{"ok": true, "agents": [{"name": "Hermes Conductor", "status": "ONLINE"}, ...]}` |

### 2. Core System & Macro Endpoints

| Kaedah | Laluan Endpoint | Penerangan |
|:---:|:---|:---|
| `GET` | `/health` | Pemeriksaan kesihatan aplikasi bagi orkestrasi perkhidmatan. |
| `GET` | `/metrics` | Metrik prestasi format Prometheus (CPU, RAM, Bilangan Permintaan). |
| `GET` | `/api/stats` | Telemetri masa-nyata perkakasan PC hos (CPU %, RAM %, Penggunaan Disk). |
| `GET` | `/api/stream/telemetry` | Penstriman Server-Sent Events (SSE) pada frekuensi 1Hz. |
| `GET` | `/api/processes` | Senarai 15 proses teratas menggunakan sumber memori tertinggi. |
| `POST` | `/api/kill/{pid}` | Menamatkan proses tertentu secara paksa (*taskkill /F*). |
| `POST` | `/api/macro/{name}` | Melancarkan skrip makro sistem (`clean_temp`, `lock_pc`, `cleanup_zombies`, `sync_webhook`). |

### 3. File System & Security Endpoints

| Kaedah | Laluan Endpoint | Penerangan |
|:---:|:---|:---|
| `GET` | `/api/files?path=...` | Mendapatkan senarai folder dan fail dalam direktori yang ditentukan. |
| `POST` | `/api/files/read` | Membaca kandungan fail teks (had keselamatan: ≤2MB). |
| `POST` | `/api/files/write` | Menulis kandungan baharu ke dalam fail berserta sandaran automatik. |
| `GET` | `/api/forensics/logs` | Mengambil log keselamatan sistem Windows Event Log. |
| `POST` | `/api/threat/scan` | Mengimbas persekitaran bagi mengesan proses berniat jahat atau port terdedah. |

### 4. Full-Duplex WebSocket Protocols

| Endpoint | Protokol | Format Mesej | Fungsi & Skop Operasi |
|:---|:---|:---|:---|
| `/ws/terminal` | WebSocket | JSON + ANSI Bytes | Sesi shell interaktif PowerShell 7 dengan kawalan saiz terminal dinamik (`resize`). |
| `/ws/browser` | WebSocket | JSON + Base64 JPEG | Penstriman bingkai paparan Chromium Playwright bersama penangkapan peristiwa klik & taip. |
| `/ws/swarm` | WebSocket | JSON | Pengagregatan degupan jantung (*heartbeat*) dan log operasi pelbagai ejen serentak. |
| `/ws/audio` | WebSocket | Binary PCM + JSON | Saluran audio dua hala untuk analisis suara VAD dan transkripsi segera. |
| `/ws/hitl` | WebSocket | JSON | Pengurusan intervensi manusia (Human-in-the-Loop) untuk kelulusan arahan berisiko tinggi. |

---

## 🔒 Telegram Mini App & Cloudflare Persistence Architecture

Salah satu ciri paling kritikal sistem ini ialah **sifar gangguan pada capaian Telegram Menu Button**. Sistem ini menggunakan seni bina berikut:

```
[Telegram Client] ──► [https://*.trycloudflare.com] ──► [cloudflared.exe (PID 15260)] ──► [127.0.0.1:9220 (Uvicorn)]
```

### 1. Arkitektur Pemisahan Token (Split-Token Protocol)
- **`TELEGRAM_BOT_TOKEN` (Outbound Sahaja)**: Digunakan oleh Hermes-WebApp semata-mata untuk menghantar makluman amaran, notifikasi intervensi HITL, dan penetapan `setChatMenuButton`. Ia **TIDAK PERNAH** menjalankan sebarang proses *polling* (`getUpdates`), menghapuskan sepenuhnya isu ralat HTTP 409 Conflict.
- **`GATEWAY_TOKEN` (Inbound Polling)**: Diuruskan oleh proses berasingan (**Hermes Gateway**) untuk menerima mesej teks pengguna secara berasingan.

### 2. Automasi Terowong Tanpa Gangguan (`cloudflare_webhook_updater.py`)
Skrip `scripts/cloudflare_webhook_updater.py` mengendalikan kesinambungan capaian secara autonomi:
1. Membuka subprocess `cloudflared tunnel --url http://localhost:9220`.
2. Menapis URL dinamik yang dijana (`https://*.trycloudflare.com`).
3. Mengemaskini pembolehubah `WEBAPP_URL` di dalam fail `.env`.
4. Memanggil Telegram API `https://api.telegram.org/bot<TOKEN>/setChatMenuButton`:
   ```json
   {
     "menu_button": {
       "type": "web_app",
       "text": "Open Hermes OS",
       "web_app": {
         "url": "https://shoulder-exercise-expressed-volume.trycloudflare.com"
       }
     }
   }
   ```
5. Apabila pelayan Uvicorn lokal dimulakan semula (contohnya selepas kemaskini kod), `cloudflared.exe` kekal berjalan dan menyambung semula trafik ke port 9220 serta-merta tanpa mengubah URL awam Telegram.

---

## 🎨 The "Anti-AI Slop" Design System

Antaramuka Hermes-WebApp dibina mengikut piawaian reka bentuk elit yang menolak sebarang bentuk "AI slop" biasa:

1. **Warna Dasar OLED Murni**:
   - Background: Pure Black (`#000000`).
   - Cards & Containers: Zinc 900/950 (`rgba(255,255,255,0.03)` dengan sempadan tajam 1px `rgba(255,255,255,0.08)`).
   - Aksen Rasmi Doh-Nut: Frosting Pink (`#ef9fbd`) dan Mint Green (`#10b981`).
2. **Tipografi Berdisiplin**:
   - Menggunakan fon berstruktur monokrom gred industri (**JetBrains Mono** dan **Inter**).
   - Penggunaan `font-variant-numeric: tabular-nums` pada semua nilai mata wang (RM) dan nombor metrik bagi menghalang peralihan jajaran teks (*layout shifts*).
3. **Ikonografi Vektor Profesional**:
   - Sifar penggunaan emotikon kartun sebagai ikon navigasi teras.
   - Wajib menggunakan SVG vektor berprestasi tinggi (**Lucide Icons**) dengan ketebalan strok konsisten 1.5px - 2px.
4. **Kekangan Skrin 100vh & Tiada Limpahan (*Zero Overflow*)**:
   - Dioptimumkan secara khusus untuk paparan peranti bimbit (iPhone 14 standard: 390px x 844px).
   - Menghormati safe area Telegram Mini App via `--tg-viewport-height`.
   - Modul bertindak sebagai tindanan penuh skrin (*full-screen slide-up modal*) menggunakan transisi CSS cecair:
     ```css
     .module-overlay {
         transform: translateY(100%);
         transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
     }
     .module-overlay.active {
         transform: translateY(0);
     }
     ```
5. **Zero-Jitter Button Engine (Emil Kowalski Craft Standard)**:
   - **Punca Jitter Diasingkan**: Penghapusan kelas `.glass` daripada 52 butang/kawalan interaktif bagi mengelakkan perlanggaran antara enjin fizik `MagicBento` dan transformasi butang.
   - **Kekangan Selector `MagicBento`**: Enjin kad bento dihadkan hanya menyasarkan kad statik (`.card:not(button):not(.btn)`), menghapuskan pengiraan `translate(magnetX, magnetY)` pada elemen boleh-klik.
   - **Maklum Balas Haptik/Taktil**: Menambah `:active { transform: scale(0.97); }` dengan transisi `transform 0.1s ease` bagi memberikan klik yang responsif dan mantap tanpa getaran kursor.
   - **Pengasingan Hover Mudah Alih**: Semua kesan `:hover` dikunci di dalam `@media (hover: hover) and (pointer: fine)` bagi mengelakkan butang "terlekat hover" pada skrin sentuh telefon pintar.
6. **Mobile-First Zero-Overlap Architecture**:
   - **Kelegaan Bilah Dok Bawah (Safe Area Clearance)**: Kontena `main` menggunakan `padding-bottom: calc(140px + env(safe-area-inset-bottom, 28px))` — memastikan butang tindakan terendah berada sekurang-kurangnya 20px di atas bilah dok bawah (`#bottom-dock`) dan bilah navigasi OS.
   - **Pencegahan Ranapan Flex**: Kontena log dan penstriman (seperti `Agent Stream`) dikunci dengan `min-height: 180px; flex-shrink: 0; max-height: 240px`, menghalang elemen daripada dihimpit sehingga 0px pada viewport peranti kecil (360x740 Android).
   - **Grid Pelancar Tindakan 3-Lajur**: Pada skrin `< 640px`, grid butang bertukar daripada 6-lajur kepada `grid-template-columns: repeat(3, 1fr)` dengan `min-height: 52px`, saiz fon `10px`, dan `padding: 8px 4px` bagi menjamin tiada pertindihan teks atau ikon.
   - **Kelegaan Tatalan Senarai**: Semua senarai tatalan (`.kanban-column-body`, senarai produk, senarai log) mempunyai `padding-bottom: 36px` bagi mengelakkan item terakhir terpotong.

---

## 🚀 Panduan Pemasangan & Pelancaran (Installation & Runbook)

### 1. Keperluan Sistem (Prerequisites)
- **Sistem Operasi**: Windows 10/11 (Disyorkan PowerShell 7 / `pwsh.exe`)
- **Python**: Versi 3.11+
- **Google Chrome**: Profil 50 dikonfigurasi (`thisisdohnut@gmail.com`)
- **Cloudflared CLI**: `cloudflared.exe` terpasang dalam PATH
- **Telegram Bot**: Token bot sah diperoleh daripada @BotFather

### 2. Langkah Pemasangan Pantas

```powershell
# 1. Navigasi ke direktori projek
cd C:\Users\megat\Hermes-WebApp

# 2. Aktifkan persekitaran maya Python
C:\Users\megat\AppData\Local\hermes\hermes-agent\venv\Scripts\Activate.ps1

# 3. Pasang kebergantungan (sekiranya belum terpasang)
pip install -r requirements.txt

# 4. Sahkan konfigurasi fail .env
# Pastikan TELEGRAM_BOT_TOKEN dan PORT=9220 ditetapkan
Get-Content .env

# 5. Lancarkan pelayan Hermes-WebApp
python main.py
```

### 3. Pelancaran Terowong Cloudflare & Sinkronisasi Menu Telegram

```powershell
# Jalankan skrip pembaharuan automatik terowong
python scripts/cloudflare_webhook_updater.py
```

### 4. Menjalankan Suite Ujian Regresi (Pytest)

```powershell
# Jalankan keseluruhan sut ujian backend
pytest -v

# Ujian khusus router Doh-Nut
pytest tests/test_dohnut_api.py -v
```

---

## 📁 Struktur Fail Projek (Project Tree)

```
C:\Users\megat\Hermes-WebApp/
├── main.py                             # Titik masuk utama (Pengesan ketersediaan port dinamik 9220)
├── requirements.txt                    # Kebergantungan Python (FastAPI, Uvicorn, Playwright, PySide6)
├── pytest.ini                          # Konfigurasi pengujian pytest
├── conftest.py                         # Konfigurasi persekitaran ujian global
├── .env                                # Konfigurasi rahsia (Token Telegram, Port 9220, URL Terowong)
├── .env.example                        # Templat rujukan pembolehubah persekitaran
├── .env.mcp.example                    # Templat rujukan pembolehubah MCP server
├── README.md                           # Dokumen spesifikasi sistem lengkap (v3.6.0)
├── CHANGELOG.md                        # Rekod versi dan log perubahan kronologi
├── GEMINI.md                           # Memori operasi tempatan ejen konduktor
├── social_autopilot.db                 # Pangkalan data SQLite draf promosi sosial tempatan
│
├── backend/
│   ├── main.py                         # Aplikasi FastAPI utama, lifespan, middleware & pelindung
│   ├── config.py                       # Pemuat konfigurasi persekitaran
│   ├── observability.py                # Pembalak berstruktur (JSONL), metrik Prometheus & amaran TG
│   ├── bot_bridge.py                   # Penghantar mesej keluar Telegram (Outbound-only)
│   │
│   ├── routers/
│   │   ├── dohnut.py                   # Router All-in-1 Mission Control Doh-Nut & WebBridge
│   │   ├── system.py                   # Router statistik teras, penjelajah fail, dan makro PC
│   │   ├── swarm.py                    # Router pengurusan dan penjejakan ejen AI
│   │   └── audio.py                    # Router pemprosesan suara & arahan audio STEM
│   │
│   ├── services/
│   │   ├── swarm_manager.py            # Kitaran hayat ejen, status proses, dan agregasi log
│   │   └── audio_engine.py             # Enjin VAD dan penghurai arahan suara CLI
│   │
│   └── websockets/
│       ├── terminal.py                 # /ws/terminal — Penstriman ConPTY PowerShell 7
│       ├── browser.py                  # /ws/browser — Penstriman bingkai Chromium Playwright
│       ├── swarm.py                    # /ws/swarm — Telemetri degupan jantung masa-nyata
│       ├── audio.py                    # /ws/audio — Penstriman audio PCM dua hala
│       └── hitl.py                     # /ws/hitl — Saluran intervensi kebenaran manusia
│
├── static/
│   ├── index.html                      # Single Page Application (SPA) — OLED Bento-Box 16-Modul (Zero-Jitter & Zero-Overlap)
│   ├── manifest.json                   # Manifest PWA untuk integrasi Telegram Mini App
│   └── icons/                          # Aset ikon resolusi pelbagai (72px - 512px)
│
├── docs/                               # Dokumentasi Divio 4-Quadrant
│   ├── README.md                       # Master documentation index hub
│   ├── PRD.md                          # Product Requirements Document (v3.6.0)
│   ├── ARCHITECTURE.md                 # Technical Architecture Specification (v3.6.0)
│   ├── AGENTS.md                       # Autonomous Agent Operational Handbook (v3.6.0)
│   ├── DESIGNS.md                      # UI/UX Specification (Anti-AI Slop & Emil Kowalski Standard)
│   ├── API.md                          # REST & WebSocket API Contract
│   ├── DEPLOYMENT.md                   # Production deployment guide (NSSM & systemd)
│   ├── SECURITY.md                     # Sovereign security & split-token protocol
│   ├── SKILLS.md                       # Specialized agent skills registry
│   ├── TROUBLESHOOTING.md              # Runtime diagnostic & runbook
│   ├── n8n/                            # Alur kerja automasi JSON n8n
│   ├── superpowers/                    # Pelan arkitektur & rekod reka bentuk
│   └── archive/                        # Semakan bersejarah, perancangan, dan patch
│
├── tools/
│   └── mcp/                            # Konfigurasi & skrip pemasangan Model Context Protocol
│       ├── README-MCP-Installation.md
│       └── README-MCP-INSTALL-PACKAGE.md
│
├── var/                                # Piawaian FHS 3.0 — Pengasingan Runtime & Data Berubah
│   ├── log/                            # Fail log operasi dan jejak audit
│   ├── run/                            # PID files dan runtime locks
│   ├── lib/                            # Data dinamik berterusan aplikasi
│   └── spool/                          # Barisan mesej dan tugasan pemprosesan
│
├── scripts/
│   ├── cloudflare_webhook_updater.py   # Pengurus terowong Cloudflare & pengemaskini Chat Menu Button
│   ├── setup_telegram_menu.py          # Utiliti pendaftaran butang menu Telegram bot
│   ├── generate_icons.py               # Penjana aset ikon PWA
│   ├── encrypt_config.py               # Enkripsi fail .env menggunakan utiliti age
│   └── ai_labs_dispatcher.py           # Pengurus fokus dan pelancaran 10 Google AI Labs
│
├── deploy/
│   ├── hermes-webapp.service           # Unit konfigurasi systemd (Linux / WSL2)
│   └── Install-HermesWebAppService.ps1 # Skrip pemasangan servis Windows (NSSM)
│
└── tests/
    ├── test_dohnut_api.py              # Ujian suite Doh-Nut Mission Control & AI Labs (5/5 PASS)
    ├── test_system_api.py              # Ujian integriti endpoint sistem
    ├── test_swarm_api.py               # Ujian endpoint pengurusan swarm
    ├── test_audio_api.py               # Ujian pemprosesan audio
    └── test_websockets_e2e.py          # Ujian sambungan hujung-ke-hujung WebSocket
```

---

## 🛡️ Sovereign Security & Zero-Trust Protocol

1. **Pengasingan Mutlak Sandbox**: Sebarang fail sensitif (`.env`, `.git`, fail pangkalan data) dilindungi daripada capaian terbuka melalui senarai putih (*whitelist*) ketat dalam endpoint `/api/files`.
2. **Kalis-Ranap Tanpa Kunci Fail Pelayar**: Integrasi media sosial dilakukan melalui port **10087 (GangNiaga WebBridge)** tanpa cuba membaca secara paksa fail pangkalan data SQLite Chrome yang sedang dikunci.
3. **Penyelia Proses Zombie (Process Hygiene)**: Sistem menguatkuasakan penutupan rapi bagi setiap subprocess yang dibuka untuk memastikan sifar beban RAM atau kebocoran pemprosesan (*memory leak*) pada hos Windows.

---

## 🤝 Hubungan Ekosistem Projek Berkaitan

- **Doh-Nut Storefront (`G:\Doh-Nut`)**: Aplikasi e-dagang pelanggan utama berasaskan Next.js 16 App Router & Bun.
- **GangNiaga WebBridge (`D:\GangNiaga-WebBridge`)**: Pelayan kawalan pelayar Chrome Profile 50 dua hala (Port 10087).
- **Hermes Gateway (`~/.hermes`)**: Ejen autonomi perisikan teras yang bertindak sebagai pemikir utama sistem.
- **Hermes Obsidian Vault (`C:\Users\megat\ObsidianVault\Hermes-Obsidian`)**: Pangkalan data pengetahuan hierarki dan MOC operasi perniagaan.

---

<div align="center">
  <b>HERMES OS & DOH-NUT SOVEREIGN MISSION CONTROL — BUILT WITH PRECISION FOR SOVEREIGN ENTERPRISE</b>
</div>
