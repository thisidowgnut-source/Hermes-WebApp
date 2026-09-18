---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — REST & WebSocket API Contract"
document_id: "HERMES-WEBAPP-API-001"
version: "3.9.0"
last_updated: "2026-09-16 14:35:00 MYT"
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
| **`3.9.0`** | 2026-09-16 14:35:00<br>`2026-09-16T06:35:00Z` | Antigravity Conductor | Agent-Reach 15-Platform Internet Router Ingestion Engine (`/api/reach/status`, `/api/reach/read-url`, `/api/reach/youtube-transcript`, `/api/reach/rss`, `/api/reach/ingest-to-omnichannel`). | `backend/services/reach_engine.py`, `backend/routers/reach.py`, `backend/main.py`, `static/index.html`, `docs/API.md` | Pytest 100% pass (292/292 tests green). |
| **`3.8.0`** | 2026-09-16 13:45:00<br>`2026-09-16T05:45:00Z` | Antigravity Conductor | Swarm Delegation (`/api/swarm/delegate`), Comprehensive Health (`/api/health/comprehensive`), Traces (`/api/traces`), and Omnichannel Validation/Audit APIs. | `backend/routers/social.py`, `backend/routers/swarm.py`, `backend/routers/system.py`, `docs/API.md` | Pytest 100% pass (275+ tests). |
| **`3.7.0`** | 2026-09-16 07:31:00<br>`2026-09-16T07:31:00+08:00` | Mission API Specialist | Task 6 Remote Operations: Expose Mission APIs, Durable Events, and Authenticated Event Streaming with single-use tickets. | `backend/services/mission_service.py`, `backend/routers/missions.py`, `backend/websockets/missions.py`, `backend/main.py`, `docs/API.md` | 12/12 passing in `test_mission_api.py` & `test_mission_events.py` (60/60 comprehensive suite). |
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
Menghantar draf terpilih ke tab aktif Chrome Profile 50 via GangNiaga WebBridge (port 10087) sebagai **bantuan pelayar (browser assistance)** sehingga pengesahan resit platform (platform receipt verification) dilaksanakan sepenuhnya mengikut spesifikasi [docs/PRD.md](file:///C:/Users/megat/Hermes-WebApp/docs/PRD.md).
- **Payload:** `{"platform": "tiktok", "content": "Skrip video..."}`
- **Response:** `{"status": "dispatched", "platform": "tiktok", "port": 10087, "receipt_pending": true}`

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

### 1.4 Mission Control & Remote Operations Endpoints (`/api/missions/*`, `/api/capabilities`)

#### `POST /api/missions`
Mencipta misi baharu secara *idempotent*. Mengesahkan profil projek dan ejen dalam `ProjectRegistry`. Menguntukkan rekod `mission_run` dan melancarkan `AgySessionManager` secara tak segerak (*asynchronous*).
- **Security:** Memerlukan sesi operator sah (`hermes_session` cookie / `X-Session-Token`) + pengepala `X-CSRF-Token`.
- **Request Body (`CreateMissionRequest`):**
  ```json
  {
    "project_slug": "doh-nut",
    "title": "Review next TikTok campaign",
    "objective": "Prepare only. Do not publish.",
    "primary_executor": "agy",
    "agent_profile": "dohnut-social-autopilot",
    "idempotency_key": "11111111-1111-1111-1111-111111111111"
  }
  ```
- **Responses:**
  - `201 Created`: Penciptaan misi baharu berjaya.
    ```json
    {
      "mission_id": "22222222-2222-2222-2222-222222222222",
      "state": "queued",
      "status": "queued",
      "run_id": "33333333-3333-3333-3333-333333333333",
      "correlation_id": "11111111-1111-1111-1111-111111111111",
      "next_action": "Awaiting executor slot"
    }
    ```
  - `200 OK`: Ulangan *idempotent* (*replay*) dengan kunci sama dan operator sama (mengembalikan snapshot sedia ada tanpa menduplikasi proses).
  - `401 Unauthorized`: Ketiadaan atau tamat tempoh sesi operator.
  - `403 Forbidden`: Token CSRF hilang atau tidak sepadan.
  - `404 Not Found`: `project_slug` atau `agent_profile` tidak sah dalam pendaftaran.
  - `429 Too Many Requests`: Melebihi had kadar panggilan (`rate_limiter`).

#### `GET /api/missions`
Menyenaraikan semua misi aktif dan bersejarah yang boleh dilihat oleh operator semasa.
- **Security:** Memerlukan sesi operator sah.
- **Responses:** `200 OK` (Senarai JSON `list[dict]`), `401 Unauthorized`.

#### `GET /api/missions/{id}`
Mendapatkan rekod penuh status terkini misi berasaskan UUID.
- **Security:** Memerlukan sesi operator sah.
- **Responses:** `200 OK` (Snapshot misi), `404 Not Found` (Misi tidak wujud), `401 Unauthorized`.

#### `POST /api/missions/{id}/turns`
Menghantar arahan atau mesej giliran (*turn*) baharu kepada misi yang sedang berjalan.
- **Security:** Memerlukan sesi operator sah + `X-CSRF-Token`.
- **Request Body (`CreateTurnRequest`):**
  ```json
  {
    "message": "Use the approved brand facts and return a review packet.",
    "idempotency_key": "44444444-4444-4444-4444-444444444444"
  }
  ```
- **Responses:**
  - `202 Accepted`:
    ```json
    {
      "turn_id": "55555555-5555-5555-5555-555555555555",
      "mission_id": "22222222-2222-2222-2222-222222222222",
      "sequence": 2,
      "state": "queued"
    }
    ```
  - `404 Not Found`: Misi tidak dijumpai.
  - `403 Forbidden`: Kegagalan CSRF.
  - `429 Too Many Requests`: Melebihi had kadar giliran.

#### `POST /api/missions/{id}/cancel`
Membatalkan larian aktif (`agy_manager.cancel_run`) dan menukar status misi ke `cancelled`.
- **Security:** Memerlukan sesi operator sah + `X-CSRF-Token`.
- **Responses:** `200 OK` (`{"status": "cancelled"}`), `404 Not Found`, `403 Forbidden`.

#### `GET /api/missions/{id}/events`
Membaca peristiwa tahan lasak (*durable events*) dari lejar SQLite mengikut turutan jujukan monotonik `sequence > after_sequence`.
- **Query Parameter:** `after_sequence` (integer, lalai: `0`).
- **Security:** Memerlukan sesi operator sah.
- **Responses:** `200 OK` (Senarai peristiwa tertib `list[dict]`), `404 Not Found`.

#### `GET /api/capabilities`
Mendapatkan senarai profil keupayaan (*capability profiles*) yang dibenarkan daripada konfigurasi orkestrasi defaults.
- **Responses:** `200 OK` (`list[dict]`).

---

### 1.5 Multi-Agent Swarm Delegation Endpoints (`/api/swarm/*`)

#### `POST /api/swarm/delegate`
Mendelegasikan matlamat tahap tinggi (*high-level goal*) kepada ejen orkestrator (`role="orchestrator"`) yang menguruskan beberapa sub-ejen pekerja serentak dengan mod matlamat autonomi (*Goal Mode*).
- **Payload:**
  ```json
  {
    "goal": "Lancarkan Kempen Donut Viral Petang",
    "orchestrator_name": "Chief-Orchestrator",
    "goal_mode": true,
    "subtasks": [
      {"role": "researcher", "name": "Trend-Analyst", "task": "Kaji tag trending TikTok F&B"},
      {"role": "copywriter", "name": "Copy-Gen", "task": "Jana skrip Khairul Aming formula"}
    ]
  }
  ```
- **Responses:** `200 OK` (`{"status": "success", "delegation": {...}}`), `400 Bad Request` (jika mengandungi metacharacter bahaya).

#### `GET /api/swarm/delegations`
Mengembalikan senarai semua orkestrasi matlamat delegasi aktif dan bersejarah.
- **Responses:** `200 OK` (`{"status": "success", "count": N, "delegations": [...]}`).

#### `GET /api/swarm/delegation/{delegation_id}`
Mendapatkan snapshot terperinci status sesebuah delegasi matlamat bersama senarai sub-tugasan.

---

### 1.6 System Observability & Comprehensive Health (`/api/health/*`, `/api/traces`)

#### `GET /api/health/comprehensive`
Pemeriksaan kesihatan mendalam merangkumi 5 komponen teras sistem:
- **System**: CPU %, RAM %, Disk Free GB, System Uptime.
- **SQLite Durable Queue**: Bilangan tugasan `pending`, `processing`, `completed`.
- **SQLite Social DB**: Status sambungan dan bilangan draf sedia ada.
- **Swarm**: Bilangan ejen aktif (*running*) dan jumlah keseluruhan ejen.
- **GangNiaga WebBridge**: Ping ke `http://127.0.0.1:10087/health` (status: `connected` atau `offline`).
- **Responses:** `200 OK` (`{"status": "healthy"|"degraded", "checks": {...}, "timestamp": ...}`).

#### `GET /api/traces`
Mengagregatkan aliran peristiwa operasi masa-nyata daripada Durable Scheduler, log ejen Swarm Manager, dan Mission Store.
- **Query Parameter:** `limit` (integer, lalai: `50`).
- **Responses:** `200 OK` (`{"traces": [...], "count": N, "timestamp": ...}`).

---

### 1.7 Social Omnichannel Validation & Audit Trail (`/api/social/*`)

#### `POST /api/social/generate-omnichannel`
Menjana pakej kandungan serentak untuk FB, IG, TikTok, dan YouTube, lengkap dengan objek validasi `validation` mengikut spesifikasi platform (auto-trim sempadan perkataan untuk X 280 aksara, nisbah 9:16 untuk TikTok & Shorts).
- **Responses:** `200 OK` (`{"draft_id": 1, "validation": {...}, "facebook": ..., "tiktok": ...}`).

#### `POST /api/social/omnichannel-action`
Meluluskan (`action="approve"`) atau menolak (`action="reject"`) draf omnichannel dengan catatan penyemak (`reviewer_notes`) dan merekodkan transaksi secara kekal ke dalam lejar `omnichannel_audit_log`.
- **Payload:**
  ```json
  {
    "draft_id": 1,
    "action": "approve",
    "reviewer_notes": "Lulus untuk slot minum petang 4:30 PM",
    "operator_id": "operator-megat"
  }
  ```
- **Responses:** `200 OK` (`{"status": "success", "audit_id": 1, "new_status": "approved", ...}`).

#### `GET /api/social/omnichannel-drafts/{draft_id}/history`
Membaca rekod jejak audit penuh bagi sesuatu draf media sosial untuk pematuhan Sovereign Markdown & Audit Standard (SMS-v1.0).

---

### 1.8 Agent-Reach Internet Ingestion Endpoints (`/api/reach/*`)

Menghubungkan penghala keupayaan internet 15-platform (YouTube, Jina Reader, RSS, V2EX, GitHub) terus ke enjin viral dan draf media sosial.

#### `GET /api/reach/status`
Memeriksa status dan backend aktif bagi kesemua 15 saluran internet Agent-Reach (`yt-dlp`, `Jina Reader`, `feedparser`, dsb).
- **Response:**
  ```json
  {
    "status": "success",
    "data": {
      "status": "online",
      "engine": "agent-reach-cli",
      "platforms": {
        "youtube": {"status": "ok", "active_backend": "yt-dlp"},
        "web": {"status": "ok", "active_backend": "Jina Reader"}
      }
    }
  }
  ```

#### `POST /api/reach/read-url`
Menyedut mana-mana artikel atau halaman web dan menukarkannya kepada format Markdown bersih melalui Jina Reader (`r.jina.ai`) tanpa overhed headless browser.
- **Payload:** `{"url": "https://example.com/artikel-pastri", "timeout": 15.0}`
- **Response:** `{"status": "success", "title": "...", "content": "...", "word_count": 420}`

#### `POST /api/reach/youtube-transcript`
Mengekstrak sari kata (*subtitles*) dan metadata video YouTube secara pantas menggunakan `yt-dlp` tanpa memuat turun fail video.
- **Payload:** `{"url": "https://www.youtube.com/watch?v=...", "timeout": 30.0}`
- **Response:** `{"status": "success", "title": "...", "transcript": "...", "duration_seconds": 360, "has_subtitles": true}`

#### `POST /api/reach/rss`
Memproses suapan RSS/Atom bagi pemantauan trend berjadual secara autonomi.
- **Payload:** `{"url": "https://foodtrends.com/feed.xml", "limit": 5}`

#### `POST /api/reach/ingest-to-omnichannel`
Saluran penuh hujung-ke-hujung (*end-to-end ingestion*): Mengekstrak laman web atau sari kata YouTube, menjana 4 pakej draf media sosial (TikTok hook, IG carousel, FB, YouTube Shorts), menghasilkan thumbnail Pollinations.ai, menjalankan `SocialValidator`, dan menyimpan draf ke dalam pangkalan data SQLite `omnichannel_drafts`.
- **Payload:**
  ```json
  {
    "url": "https://www.youtube.com/watch?v=...",
    "source_type": "auto",
    "target_audience": "Usahawan & Peminat Bakeri",
    "language": "Bahasa Melayu & English",
    "tone": "Santai, berautoriti & praktikal",
    "auto_save": true
  }
  ```
- **Response:** `{"status": "success", "draft_id": 2, "topic": "...", "facebook": "...", "tiktok": "...", "validation": {...}}`

---

## 2. Full-Duplex WebSocket Protocols

| Endpoint | Subprotocol | Format Mesej | Fungsi & Skop Operasi |
|:---|:---|:---|:---|
| `/ws/missions/{mission_id}` | Mission Stream | JSON Tickets + Events | Penstriman peristiwa masa-nyata misi dengan pengesahan tiket sekali guna (*one-time ticket*) dan main semula kursor (*cursor replay*). |
| `/ws/terminal` | ConPTY | Raw ANSI Bytes + JSON | Sesi shell interaktif PowerShell 7 dengan kawalan saiz terminal dinamik (`resize`). |
| `/ws/browser` | Playwright | JSON + Base64 JPEG | Penstriman bingkai Chromium Playwright bersama penangkapan peristiwa klik & taip. |
| `/ws/swarm` | Telemetry | JSON Broadcast | Pengagregatan degupan jantung (*heartbeat*) dan log operasi pelbagai ejen serentak. |
| `/ws/audio` | Audio Engine | Binary PCM + JSON | Saluran audio dua hala untuk analisis suara VAD dan transkripsi segera. |
| `/ws/hitl` | HITL Engine | JSON | Pengurusan intervensi manusia (Human-in-the-Loop) untuk kelulusan arahan berisiko tinggi. |

### 2.1 Protokol Sambungan Misi (`/ws/missions/{mission_id}`)

1. **Jabat Tangan & Pengesahan:**
   - Pelanggan membuka sambungan WebSocket.
   - Pelanggan WAJIB menghantar mesej JSON pertama dalam tempoh 10 saat:
     ```json
     {"ticket": "wst_abcdef123456...", "after_sequence": 0}
     ```
   - Pelayan mengesahkan tiket sekali-guna (*single-use ticket*) via `session_auth_service.consume_websocket_ticket(ticket)`.
   - Sekiranya tiket tidak sah, tamat tempoh, atau telah digunakan: pelayan menutup sambungan dengan kod **`4401`** (`Unauthorized ticket`).
   - Sekiranya misi tidak dijumpai: pelayan menutup sambungan dengan kod **`4404`** (`Mission not found`).
2. **Main Semula Kursor (*Cursor Replay*):**
   - Pelayan membaca rekod peristiwa tahan lasak dengan `sequence > after_sequence` daripada stor dan menghantarnya satu per satu ke soket.
3. **Penstriman Masa-Nyata (*Live Fan-Out*):**
   - Pelayan mendaftarkan pelanggan ke antrian siaran (*in-memory subscriber queue*) `MissionService`.
   - Setiap peristiwa baharu dihantar secara langsung kepada pelanggan.
4. **Kebersihan Pemutusan Sambungan:**
   - Pemutusan sambungan oleh pelanggan dikesan secara anggun tanpa merosakkan lejar atau membatalkan misi hos.

