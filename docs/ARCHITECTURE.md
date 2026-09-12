---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — System Architecture Specification"
document_id: "HERMES-WEBAPP-ARCH-001"
version: "3.6.0"
last_updated: "2026-09-12 16:35:00 MYT"
maintainer: "GangBo Sovereign Architect"
classification: "MISSION-CRITICAL // ARCHITECTURE CORE"
lifecycle_status: "PRODUCTION / STABLE"
---

# 🏗️ Hermes OS & Doh-Nut Sovereign Mission Control — System Architecture Specification

> **Technical Architecture Blueprint detailing the system topology, dual-plane IPC communication, full-duplex WebSocket hubs, Cloudflare edge tunneling, GangNiaga WebBridge integration, and zero-trust security model.**

---

## 📜 Audit & Revision Ledger

| Version | Timestamp (MYT / ISO) | Author / Agent | Root Cause / Rationale | Scope & Architectural Changes | Empirical Validation Proof |
|:---|:---|:---|:---|:---|:---|
| **`3.6.0`** | 2026-09-12 16:35:00<br>`2026-09-12T08:35:00Z` | Antigravity Conductor | Penstrukturan FHS 3.0 (Direktori PRO), Kemasan Butang Emil Kowalski (Zero-Jitter), dan Arkitektur Mobile-First Sifar-Bertindih. | `static/index.html`, `var/`, `tools/mcp/`, `docs/ARCHITECTURE.md` | 0 jitter butang pada hover, 0 bertindih pada viewport 390x844 & 360x740, FHS 3.0 layout 13 fail root. |
| **`3.5.0`** | 2026-09-12 15:22:00<br>`2026-09-12T07:22:00Z` | Antigravity Conductor | Penyatuan All-in-1 Mission Control Doh-Nut ke dalam Hermes-WebApp tanpa mengganggu Telegram Menu Button. | `backend/routers/dohnut.py`, `backend/main.py`, `static/index.html`, `docs/ARCHITECTURE.md` | 5/5 API Endpoints 200 OK, Chrome DevTools MCP Desktop & Mobile (390px) verified. |
| **`3.0.0`** | 2026-07-27 18:00:00<br>`2026-07-27T10:00:00Z` | Hermes Dev Squad | Reka bentuk semula Bento-Box Dashboard, pembetulan CSS overlay z-index, integrasi Termux Hacker's Keyboard. | `static/index.html`, `backend/websockets/terminal.py` | 84/84 Pytest suite passed, 14 modul UI lulus ujian headless DOM. |
| **`1.0.0`** | 2026-07-20 12:00:00<br>`2026-07-20T04:00:00Z` | Megat / Bo | Spesifikasi asal seni bina Hermes OS WebApp. | FastAPI + WebSockets + Cloudflare Tunnel | PWA & Telegram WebApp MVP. |

---

## 1. High-Level Architectural Topology

Seni bina sistem berasaskan model **Localized Control Plane** di mana teras pengiraan, pangkalan data, dan eksekusi berada 100% pada persekitaran hos Windows tempatan. Trafik awam disalurkan secara selamat melalui Cloudflare Secure Edge Tunnel terus ke pelayan FastAPI tempatan pada port `9220`.

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Access Interfaces"]
        TGM["Telegram Mini App (Mobile 390px)"]
        DKP["Desktop PWA (Chromium/Edge)"]
    end

    subgraph EdgeLayer ["Cloudflare Secure Edge"]
        CFT["Cloudflare Secure Tunnel (HTTPS/WSS)"]
        CFD["cloudflared.exe Daemon (Host PID 15260)"]
    end

    subgraph BackendLayer ["FastAPI Local Control Plane (127.0.0.1:9220)"]
        UVI["Uvicorn Async Worker Server"]
        
        subgraph REST_Routers ["REST API Routing Engine"]
            R_DOH["/api/dohnut/* (Baking, Social, Swarm, Labs)"]
            R_SYS["/api/stats, /api/processes, /api/macro/*"]
            R_FIL["/api/files (Secure Directory Explorer)"]
            R_SWM["/api/swarm (Multi-Agent Management)"]
            R_AUD["/api/audio (VAD & Voice CLI)"]
        end

        subgraph WS_Hubs ["Full-Duplex WebSocket Hubs"]
            WS_TRM["/ws/terminal (ConPTY / PowerShell 7)"]
            WS_BRW["/ws/browser (Playwright JPEG Stream)"]
            WS_SWM["/ws/swarm (Agent Heartbeat & Telemetry)"]
            WS_AUD["/ws/audio (PCM Audio & Transcripts)"]
            WS_HTL["/ws/hitl (Human-in-the-Loop Interventions)"]
        end
    end

    subgraph HostSystemLayer ["Host OS Services & Background Daemons"]
        PWS["PowerShell 7 (pwsh.exe Process)"]
        PLW["Playwright Headless Chromium Engine"]
        WBR["GangNiaga WebBridge Daemon (Port 10087)"]
        ODD["Open Design Generative Daemon (Port 7456)"]
        CH50["Google Chrome User Profile 50 (thisisdohnut@gmail.com)"]
        OBS["Obsidian Knowledge Vault (2,700+ Notes)"]
    end

    TGM -->|HTTPS/WSS| CFT
    DKP -->|HTTPS/WSS| CFT
    CFT -->|Secure Passthrough| CFD
    CFD -->|Local Proxy| UVI

    UVI --> REST_Routers
    UVI --> WS_Hubs

    WS_TRM -->|PTY IPC| PWS
    WS_BRW -->|CDP Commands| PLW
    R_DOH -->|HTTP REST| WBR
    WBR -->|DOM Injection| CH50
    R_DOH -->|HTTP REST| ODD
    R_FIL -->|Direct Read/Write| OBS
```

---

## 2. Core Subsystems & Components

### 2.1 FastAPI Orchestration Engine (`backend/main.py` & `main.py`)
- **Port Availability Fallback**:
  - Pelayan memeriksa ketersediaan port secara dinamik bermula dari `config.PORT` (`9220`), kemudian beralih kepada `9230`, `9225`, `9255`, `9290`, atau `8080` sekiranya berlaku konflik.
- **Lifespan Manager**:
  - Menginisialisasi pembalak berstruktur (`observability.py`), sambungan bot Telegram keluar (`bot_bridge.py`), dan memuatkan pembolehubah persekitaran `.env` sebelum menerima trafik.
- **Pendaftaran Router Modular**:
  - `dohnut_router` (`/api/dohnut`): Mengendalikan operasi perniagaan Doh-Nut, akaun media sosial, integrasi WebBridge, dan status skuad ejen.
  - `system_router` (`/api/stats`, `/api/macro`, `/api/files`, `/api/forensics`).
  - `swarm_router` (`/api/swarm`).
  - `audio_router` (`/api/audio`).

### 2.2 Doh-Nut Sovereign Mission Control Subsystem (`backend/routers/dohnut.py`)
- **Struktur Aliran Data (Data Pipeline)**:
  1. *Telemetry Ingestion*: Mengambil data pesanan dan hasil daripada sistem fail atau pangkalan data jualan tempatan.
  2. *Omnichannel Campaign Synthesis*: Menjana variasi draf teks berstruktur khusus untuk 6 platform media sosial dalam satu panggilan API.
  3. *WebBridge Action Dispatcher*:
     ```python
     # Alur Penyiaran WebBridge ke Profile 50
     async with httpx.AsyncClient(timeout=5.0) as client:
         resp = await client.post(
             "http://127.0.0.1:10087/action/inject",
             json={"platform": req.platform, "content": req.content, "profile": 50},
             headers={"X-API-Key": WEBBRIDGE_API_KEY}
         )
     ```
  4. *Swarm Telemetry Aggregator*: Mengesan ketersediaan nod-nod pintar tempatan (Hermes, Antigravity, WebBridge, Open Design).

### 2.3 Terminal ConPTY Subsystem (`backend/websockets/terminal.py`)
- Membuka subprocess `pwsh.exe -NoProfile -NoLogo` menggunakan modul `ptyprocess` atau Windows Pseudo-Console API (ConPTY).
- Menghapuskan pembaziran lebar jalur dengan memampatkan aksara ANSI warna terus ke klien xterm.js.
- **Penapis PTY Ping**: Mengasingkan bait arahan `0x09` (Tab) dan rentetan JSON `ping`/`pong` supaya kanvas visual terminal kekal bersih daripada cetakan teks sampah.

### 2.4 Hermes Vision Subsystem (`backend/websockets/browser.py`)
- Melancarkan instance pelayar Chromium Playwright berprestasi tinggi.
- Menangkap tangkapan skrin tetingkap aktif pada frekuensi dinamik (adaptive framerate) dan menstrimkannya dalam format Base64 JPEG.
- Mengubah koordinat sentuhan mudah alih Telegram ke koordinat tepat piksel pelayar hos:
  ```
  Normalized Mobile (X, Y) ──► Viewport Ratio Multiplier ──► Playwright mouse.click(px_X, px_Y)
  ```

### 2.5 FHS 3.0 Runtime Separation & File Hierarchy
Sistem mengamalkan piawaian pengasingan Filesystem Hierarchy Standard (FHS 3.0) bagi memastikan punca repositori kekal bersih dan operasi runtime terasing:

```mermaid
graph TD
    Root["C:\Users\megat\Hermes-WebApp (Root: 13 Files)"]
    
    subgraph RuntimeLayer ["FHS 3.0 Runtime Layer (var/)"]
        V_LOG["var/log/ — Telemetry, Audit & Access Logs"]
        V_RUN["var/run/ — PID Files & Process Locks"]
        V_LIB["var/lib/ — Dynamic Application State & Caches"]
        V_SPL["var/spool/ — Async Task & Message Queues"]
    end

    subgraph ToolsLayer ["Tools & Extensions (tools/)"]
        T_MCP["tools/mcp/ — MCP Package Guides & Installers"]
    end

    subgraph DocsLayer ["Divio 4-Quadrant Documentation (docs/)"]
        D_TUT["Tutorials: README.md (Root)"]
        D_HOW["How-To: DEPLOYMENT.md, TROUBLESHOOTING.md"]
        D_REF["Reference: ARCHITECTURE.md, API.md, DESIGNS.md, SECURITY.md"]
        D_EXP["Explanation: PRD.md, AGENTS.md, SKILLS.md"]
        D_ARC["docs/archive/ — Historical Reviews & Planning"]
        D_N8N["docs/n8n/ — JSON Workflow Blueprints"]
    end

    Root --> RuntimeLayer
    Root --> ToolsLayer
    Root --> DocsLayer
```

---

## 3. Network & Edge Tunneling Strategy

### 3.1 Mengapa Cloudflare Tunnels (Bukan Localtunnel / Ngrok)?
- **Localtunnel Limitation**: Localtunnel memaparkan halaman amaran pelindung (*interstitial warning*) yang memerlukan pengguna menekan butang sebelum laman dimuatkan. Telegram Mini App WebView tidak menyokong halaman ini, menyebabkan skrin tergantung (*infinite loading freeze*).
- **Cloudflare Edge Direct Passthrough**: `cloudflared` memberikan penamatan SSL automatik di peringkat edge Cloudflare tanpa sebarang halaman amaran, membolehkan Telegram WebApp dimuatkan serta-merta dalam <1.5 saat.

### 3.2 Dynamic Webhook & Telegram Menu Sync Engine
```mermaid
sequenceDiagram
    autonumber
    participant Updater as cloudflare_webhook_updater.py
    participant CF as cloudflared.exe (PID 15260)
    participant Edge as Cloudflare Network
    participant TG as Telegram Bot API
    participant User as Telegram Mini App Client

    Updater->>CF: Popen(["cloudflared", "tunnel", "--url", "http://localhost:9220"])
    CF->>Edge: Establishes secure TLS tunnel
    Edge-->>CF: Output URL: https://*.trycloudflare.com
    CF-->>Updater: Read stdout stream match URL pattern
    Updater->>Updater: Write WEBAPP_URL to .env
    Updater->>TG: POST /setChatMenuButton (text: "Open Hermes OS", url: tunnel_url)
    TG-->>Updater: 200 OK (Chat Menu Button Updated)
    User->>TG: Taps "Open Hermes OS" button
    TG->>Edge: Fetches https://*.trycloudflare.com
    Edge->>CF: Proxies request over edge connection
    CF->>Uvicorn: 127.0.0.1:9220 GET /
```

---

## 4. Frontend State Machine & Viewport Architecture

### 4.1 SPA Architecture & CSS Transitions
- **Bento-Box Grid Hierarchy**:
  - Bahagian Atas: Bar status nod hos & Bar input arahan langsung Hermes.
  - Bahagian Tengah: Grid tindakan pantas 6-butang + Kad Bento Doh-Nut HQ + Kad Multi-Agent Swarm.
  - Bahagian Bawah: Bilah Dok Bawah mengandungi 16 ikon subsistem.
- **Tindanan Skrin Penuh (Full-Screen Slide-Up Overlays)**:
  - Setiap modul menggunakan kelas `.module-overlay`.
  - Apabila diaktifkan (`.module-overlay.active`), modal dinaikkan menggunakan transisi `transform: translateY(0)` dengan fungsi pemasaan `cubic-bezier(0.16, 1, 0.3, 1)`.
  - Menyokong penderiaan sejarah pelayar (`history.pushState` dan `window.onpopstate`) bagi memastikan gerak isyarat leret kembali (*swipe-back*) atau butang kembali peranti bimbit menutup modal tanpa menutup Telegram Mini App.

### 4.2 Zero-Jitter Button Interaction Model (Emil Kowalski Craft Standard)
Punca utama kegoyangan/getaran butang (*button jitter*) yang dikesan sebelum ini ialah pertembungan antara enjin fizikal penjejakan tetikus `MagicBento` dan transformasi butang CSS:
1. **Pemisahan Kelas**: Menanggalkan kelas `.glass` daripada 52 elemen butang. Kelas `.glass` hanya dibenarkan pada bekas kontena statik.
2. **Kekangan Selector**: Menapis pemilih kad dalam JavaScript:
   ```javascript
   const bentoCards = document.querySelectorAll('.card:not(button):not(.btn)');
   ```
   Ini menghalang pengiraan koordinat relatif tetikus `(magnetX, magnetY)` daripada mengenakan transformasi ayunan pada elemen yang boleh diklik.
3. **Maklum Balas Taktil Cepat**:
   ```css
   button:active, .btn:active, .tab-btn:active {
       transform: scale(0.97) !important;
       transition: transform 0.1s ease !important;
   }
   ```
4. **Perlindungan Hover Skrin Sentuh**:
   Mengurung semua transformasi `:hover` dalam query media `@media (hover: hover) and (pointer: fine)` bagi memastikan peranti bimbit tidak mengalami masalah *sticky hover*.

### 4.3 Mobile-First Zero-Overlap Architecture & Safe-Area Clearance Engine
Bagi memastikan sifar pertindihan (*zero overlap*) antara komponen pada viewport peranti bimbit (390x844px dan 360x740px):
1. **Safe-Area Clearance Equation**:
   ```css
   main {
       padding-bottom: calc(140px + env(safe-area-inset-bottom, 28px)) !important;
   }
   ```
   Persamaan ini mengira ketinggian bilah dok tetap (64px) + margin terapung (24px) + kelegaan visual selamat (24px) + safe-area peranti Telegram (28px) = jumlah 140px+ clearance.
2. **Flexbox Collapse Guardrails**:
   Kontena dinamik (seperti `#agent-stream-container`) dipasang pelindung saiz ketat:
   ```css
   #agent-stream-container {
       min-height: 180px !important;
       flex-shrink: 0 !important;
       max-height: 240px !important;
   }
   ```
   Menghalang pemampatan flexbox daripada mengecilkan modul penstriman log kepada 0px apabila papan kekunci maya dinaikkan.
3. **Responsive 3-Column Touch Matrix**:
   Pada lebar `< 640px`, grid butang tindakan bertukar daripada 6 lajur kepada 3 lajur sekata (`repeat(3, 1fr)`) dengan tinggi minimum 52px bagi memastikan sasaran sentuhan jari (*touch targets*) menepati piawaian ergonomik Apple/Android (min 48px).
4. **List Scroll Extents**:
   Semua ruang senarai dalaman mempunyai `padding-bottom: 36px` untuk membolehkan item terakhir dilihat dan disentuh sepenuhnya tanpa terlindung di bawah sempadan bekas.

---

## 5. Security & Isolation Model

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SPLIT-TOKEN SECURITY PLANE                      │
│                                                                        │
│   [HERMES GATEWAY]                           [HERMES WEBAPP]           │
│   • Inbound Long-Polling                     • Outbound API Calls Only │
│   • Receives /commands                       • Sends HITL Alerts       │
│   • Token: GATEWAY_TOKEN                     • Updates Menu Button     │
│                                              • Token: WEBAPP_BOT_TOKEN │
│   ───────────────────────────────────────────────────────────────────  │
│          Zero HTTP 409 Conflict Across Independent Event Loops         │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Sandboxing Directory Traversal**: Laluan sistem fail diakses secara mutlak dengan semakan sekatan laluan induk untuk menghalang eksploitasi direktori `../..`.
2. **Kunci Fail Pelayar Defensif**: Membaca atau memanipulasi profil Google Chrome dilakukan sepenuhnya menerusi protokol REST / CDP GangNiaga WebBridge, mengelakkan ralat perkongsian pangkalan data SQLite (`database is locked`).
3. **Penyelia Proses Latar Belakang (Zombie Task Hygiene)**: Setiap arahan shell yang dijalankan oleh ejen didaftarkan ke dalam pemantau tugas latar belakang (`manage_task`) dan ditamatkan serta-merta selepas bacaan log selesai.
