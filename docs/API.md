---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — REST & WebSocket API Contract"
document_id: "HERMES-WEBAPP-API-001"
version: "3.6.0"
last_updated: "2026-09-12 16:35:00 MYT"
maintainer: "GangBo Sovereign Architect"
classification: "ENGINEERING DOCS // API SPECIFICATION"
lifecycle_status: "PRODUCTION / STABLE"
---

# 🔌 REST & WebSocket API Contract (API.md)

> **Official API Specification for Hermes OS & Doh-Nut Sovereign Mission Control.** Autonomous AI agents and client interfaces can hit these endpoints directly.

---

## 📜 Audit & Revision Ledger

| Version | Timestamp (MYT / ISO) | Author / Agent | Scope / Root Cause | Components Updated | Validation Proof |
|:---|:---|:---|:---|:---|:---|
| **`3.6.0`** | 2026-09-12 16:35:00<br>`2026-09-12T08:35:00Z` | Antigravity Conductor | Dokumentasi API lengkap merangkumi Doh-Nut Mission Control, Filesystem & 5 WebSockets. | `docs/API.md`, `backend/routers/dohnut.py` | 5/5 Doh-Nut tests passing, 0 schema errors. |
| **`3.5.0`** | 2026-09-12 15:22:00<br>`2026-09-12T07:22:00Z` | Antigravity Conductor | Penambahan 5 endpoint Doh-Nut Sovereign HQ & WebBridge publishing. | `backend/routers/dohnut.py` | 5/5 API Endpoints 200 OK. |
| **`1.0.0`** | 2026-07-20 12:00:00<br>`2026-07-20T04:00:00Z` | Megat / Bo | Spesifikasi asal endpoint asas sistem dan WebSocket terminal. | `backend/routers/system.py` | Endpoint asas berfungsi. |

---

## 1. REST Endpoints (Base URL: `http://127.0.0.1:9220`)

### 1.1 Doh-Nut Sovereign HQ Endpoints (`/api/dohnut/*`)

#### `GET /api/dohnut/stats`
Mengembalikan data telemetri kewangan jualan harian, pesanan aktif, barisan katering, baki doh, dan stok signatur.
- **Response:**
  ```json
  {
    "status": "ok",
    "revenue": 1420.50,
    "completed_orders": 34,
    "active_baking_orders": 8,
    "catering_queue": 150,
    "dough_batches": 14,
    "signature_stock": {
      "kuih_burger": 42,
      "kuih_keria": 38,
      "sambal_pedas": 25,
      "classic_glazed": 50,
      "matcha_white": 8
    }
  }
  ```

#### `POST /api/dohnut/orders`
Menambah atau mengemaskini status pesanan dalam saluran pembakar 4-tahap.
- **Payload:**
  ```json
  {
    "order_id": "#409",
    "customer": "Ahmad",
    "items": ["2x Kuih Burger", "1x Classic Glazed"],
    "stage": "preparing"
  }
  ```
- **Stages:** `preparing` | `frying` | `glazing` | `ready`

#### `POST /api/dohnut/social/generate`
Menjana teks promosi viral 6-platform berdasarkan satu topik input.
- **Payload:** `{"topic": "Combo Kuih Burger Viral RM15"}`
- **Response:** Mengandungi medan draf berasingan untuk `tiktok`, `instagram`, `threads`, `facebook`, `x`, dan `youtube`.

#### `POST /api/dohnut/social/publish-webbridge`
Menyiarkan draf terpilih secara terus ke tab aktif Chrome Profile 50 via GangNiaga WebBridge (port 10087).
- **Payload:** `{"platform": "tiktok", "content": "Skrip video..."}`
- **Response:** `{"status": "dispatched", "platform": "tiktok", "port": 10087}`

#### `GET /api/dohnut/agent-swarm/status`
Mengembalikan status sambungan 4 nod ejen teras (Hermes Conductor, Antigravity Conductor, GangNiaga WebBridge, Open Design Daemon).

#### `POST /api/dohnut/ai-labs/launch`
Memfokuskan tetingkap atau melancarkan 1 daripada 10 Google AI Labs tabs.
- **Payload:** `{"lab_id": "mixboard" | "stitch" | "putty" | "jules" | "opal" | "studio" | "notebooklm" | "flow" | "chatgpt" | "hub"}`

---

### 1.2 System & Telemetry Endpoints

#### `GET /api/stats`
Mengembalikan penggunaan CPU, RAM, dan cakera masa-nyata.

#### `GET /api/processes`
Mengembalikan senarai 15 proses teratas yang memakan memori tertinggi pada hos Windows.

#### `POST /api/kill/{pid}`
Menamatkan proses sistem tertentu secara paksa (`taskkill /F`).

#### `POST /api/macro/{macro_name}`
Melancarkan skrip makro sistem: `clean_temp`, `lock_pc`, `cleanup_zombies`, `sync_webhook`.

---

### 1.3 Secure File Explorer Endpoints

#### `GET /api/files?path=...`
Mendapatkan senarai folder dan fail dalam direktori yang ditentukan (dengan sekatan sandbox induk).

#### `POST /api/files/read`
Membaca kandungan fail teks (had keselamatan: ≤2MB).

#### `POST /api/files/write`
Menulis kandungan baharu ke dalam fail berserta sandaran automatik.

---

## 2. Full-Duplex WebSocket Protocols

| Endpoint | Subprotocol | Format Mesej | Fungsi & Skop Operasi |
|:---|:---|:---|:---|
| `/ws/terminal` | ConPTY | Raw ANSI Bytes + JSON | Sesi shell interaktif PowerShell 7 dengan kawalan saiz terminal dinamik (`resize`). |
| `/ws/browser` | Playwright | JSON + Base64 JPEG | Penstriman bingkai Chromium Playwright bersama penangkapan peristiwa klik & taip. |
| `/ws/swarm` | Telemetry | JSON Broadcast | Pengagregatan degupan jantung (*heartbeat*) dan log operasi pelbagai ejen serentak. |
| `/ws/audio` | Audio Engine | Binary PCM + JSON | Saluran audio dua hala untuk analisis suara VAD dan transkripsi segera. |
| `/ws/hitl` | HITL Engine | JSON | Pengurusan intervensi manusia (Human-in-the-Loop) untuk kelulusan arahan berisiko tinggi. |
