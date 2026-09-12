---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — Workspace Memory & Learned Rules"
document_id: "HERMES-WEBAPP-MEM-001"
version: "3.6.0"
last_updated: "2026-09-12 16:35:00 MYT"
maintainer: "GangBo Sovereign Architect"
classification: "MISSION-CRITICAL // OPERATIONAL MEMORY"
lifecycle_status: "ACTIVE"
---

# 🎼 Gemini Workspace Memory & Learned Rules (GEMINI.md)

Dokumen ini merekodkan peraturan yang dipelajari, status seni bina, dan standard operasi yang disahkan untuk projek **Hermes-WebApp** dan persekitaran kerja hos.

---

## 📜 Audit & Revision Ledger

| Version | Timestamp (MYT / ISO) | Author / Agent | Root Cause / Rationale | Code Scope & Changes | Empirical Validation Proof |
|:---|:---|:---|:---|:---|:---|
| **`3.6.0`** | 2026-09-12 16:35:00<br>`2026-09-12T08:35:00Z` | Antigravity Conductor | Penstrukturan FHS 3.0 (Direktori PRO), Penghapusan Jitter Butang (Emil Kowalski Craft), dan Arkitektur Mobile-First Sifar-Bertindih. | `static/index.html`, `var/`, `tools/mcp/`, `docs/`, `tests/test_dohnut_api.py`, `GEMINI.md` | FHS 3.0 root 13 fail, 0 jitter butang pada hover, 0 bertindih pada viewport 390x844 & 360x740, 5/5 Doh-Nut tests passing. |
| **`3.5.0`** | 2026-09-12 15:15:00<br>`2026-09-12T07:15:00Z` | Antigravity Conductor | Penyatuan All-in-1 Mission Control Doh-Nut ke dalam Hermes-WebApp tanpa mengganggu persediaan Telegram Menu Button. | `backend/routers/dohnut.py`, `backend/main.py`, `static/index.html` | 5/5 API Endpoints 200 OK, Chrome DevTools MCP Desktop & Mobile (390px) verified, Zero console errors. |
| **`3.4.0`** | 2026-09-12 02:30:00<br>`2026-09-11T18:30:00Z` | Conductor Agent | Pengesahan profil media sosial Chrome Profile 50 (`thisisdohnut@gmail.com`) dan integrasi WebBridge port 10087. | `static/index.html`, `scripts/ai_labs_dispatcher.py` | 6 platform disahkan, 62/62 Bun tests pass. |
| **`2.1.0`** | 2026-07-21 12:00:00<br>`2026-07-21T04:00:00Z` | Hermes Dev Squad | Enjin kandungan Omnichannel via n8n & GitHub shared-state staging queue. | `scripts/queue_manager.py`, `aiogram_bridge.py` | n8n asynchronous webhook loop verified. |

---

## 🛑 SOVEREIGN AUTONOMOUS EXECUTION PROTOCOL (NON-NEGOTIABLE)

1. **Sifar Penyerahan Manual (Zero Manual Hand-Off)**:
   - JANGAN SEKALI-KALI meminta pengguna menjalankan skrip `uvicorn`, pelancaran pelayan, atau pendaftaran Cloudflare Tunnel secara manual. Ejen **WAJIB** melancarkan skrip latar belakang (`run_command`) secara autonomi dan mengesahkan respons pelayan secara *real-time*.

2. **Kekangan Sifar Docker (100% Native OS Constraint)**:
   - Semua aplikasi, modul, dan servis MESTI dibina menggunakan Python 3.11 tempatan, PowerShell, `psutil`, dan SQLite secara terus di atas Windows OS tanpa kontena Docker.

3. **Pembersihan Berterusan (Resource & Task Hygiene)**:
   - Segera tamatkan sub-ejen yang selesai (`manage_subagents kill_all`) dan tugas zombie (`manage_task kill`) sebaik sahaja log disemak untuk mengelakkan pembaziran RAM dan CPU.

4. **Perlindungan Terowong Telegram (Zero Disruption)**:
   - Terowong Cloudflare (`PID 15260`) menghala terus ke `http://127.0.0.1:9220` (`https://shoulder-exercise-expressed-volume.trycloudflare.com`).
   - Dilarang sama sekali menukar port 9220 atau mematikan proses `cloudflared.exe` yang memegang URL awam Telegram Menu Button (`Open Hermes OS`).

---

## 📁 1. Standard Organisasi Fail FHS 3.0 & Kebersihan Punca (Root Hygiene)

Bagi memastikan repositori berada pada tahap kejuruteraan profesional bertaraf perusahaan:
1. **Pengasingan Data Runtime ke `var/`**:
   - `var/log/` ➔ Fail pembalak transaksi, ralat, dan telemetri (`telemetry.log`, `access.log`).
   - `var/run/` ➔ Fail pengenalan proses (`uvicorn.pid`, `cloudflared.pid`, lockfiles).
   - `var/lib/` ➔ Data dinamik aplikasi (keadaan persisten sesi, cache sementara).
   - `var/spool/` ➔ Barisan mesej dan barisan tugasan tak segerak (staging queues).
2. **Pengasingan Alatan MCP ke `tools/mcp/`**:
   - Skrip pemasangan dan panduan konfigurasi MCP server ditempatkan di `tools/mcp/`.
3. **Dokumentasi Divio 4-Quadrant di `docs/`**:
   - Tutorials di punca (`README.md`).
   - How-To Guides: `docs/DEPLOYMENT.md`, `docs/TROUBLESHOOTING.md`.
   - Reference: `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/DESIGNS.md`, `docs/SECURITY.md`.
   - Explanation: `docs/PRD.md`, `docs/AGENTS.md`, `docs/SKILLS.md`.
   - Sejarah/arkib disimpan rapi dalam `docs/archive/` dan alur kerja n8n dalam `docs/n8n/`.
4. **Had Siling Punca Direktori**:
   - Punca direktori projek (`Hermes-WebApp`) dihadkan kepada **maksimum 15 fail** (kini 13 fail teras).

---

## 🎯 2. Standard Kemasan Butang Emil Kowalski (Zero-Jitter Button Polish)

Sebarang elemen boleh klik (butang, tab, suis) **MESTI** mematuhi standard ketukangan antaramuka Emil Kowalski:
1. **PENGHARAMAN `.glass` pada Elemen Interaktif**:
   - Jangan sekali-kali meletakkan kelas `.glass` pada elemen `<button>`, `.btn`, `.tab-btn`, atau pautan interaktif. Kelas `.glass` hanya untuk bekas latar belakang statik.
2. **Kekangan Selector `MagicBento`**:
   - Enjin kad bento hanya menyasarkan elemen kad bukan kawalan: `.card:not(button):not(.btn)`. Elemen kawalan dilarang menerima pengiraan fizik magnetik `translate(magnetX, magnetY)`.
3. **Maklum Balas Taktil Responsif**:
   - Setiap butang wajib mempunyai:
     ```css
     button:active, .btn:active, .tab-btn:active {
         transform: scale(0.97) !important;
         transition: transform 0.1s ease !important;
     }
     ```
4. **Pengasingan Hover Mudah Alih**:
   - Semua penggayaan `:hover` (seperti `background-color`, `border-color`, atau pencerahan) **WAJIB** dibalut di dalam `@media (hover: hover) and (pointer: fine)` bagi mengelakkan butang melekat (*sticky hover*) pada skrin sentuh telefon.

---

## 📱 3. Arkitektur Mobile-First Sifar-Bertindih (Zero-Overlap Ergonomics)

Bagi menjamin pengalaman pengguna sempurna pada paparan peranti bimbit (iPhone 14 standard 390x844px dan Android standard 360x740px):
1. **Kelegaan Bilah Dok Bawah (Safe-Area Bottom Clearance)**:
   - Elemen `main` dan setiap kontena paparan penuh **WAJIB** mengekalkan ruang kosong di bahagian bawah:
     ```css
     main {
         padding-bottom: calc(140px + env(safe-area-inset-bottom, 28px)) !important;
     }
     ```
   - Ini memastikan elemen tindakan paling bawah berada sekurang-kurangnya 20px di atas `#bottom-dock` dan bilah leretan peranti.
2. **Pencegahan Ranapan Flex**:
   - Elemen dinamik (seperti `Agent Stream` dan konsol log) dikunci dengan:
     ```css
     #agent-stream-container {
         min-height: 180px !important;
         flex-shrink: 0 !important;
         max-height: 240px !important;
     }
     ```
   - Menghalang pengecutan ketinggian kepada 0px pada viewport peranti kecil.
3. **Grid Pelancar Tindakan 3-Lajur**:
   - Pada paparan skrin kecil (`< 640px`), grid pelancar bertukar kepada:
     ```css
     .action-launchers-grid {
         grid-template-columns: repeat(3, 1fr) !important;
     }
     ```
   - Dengan `min-height: 52px` dan `font-size: 10px` bagi mengelakkan pertindihan teks atau ikon.
4. **Kelegaan Tatalan Senarai**:
   - Semua ruang tatalan berasingan (`.kanban-column-body`, senarai produk, senarai log) mempunyai `padding-bottom: 36px` bagi mengelakkan kad terakhir tersembunyi di bawah sempadan bekas.

---

## 🍩 4. Doh-Nut Sovereign Mission Control & Social Autopilot

1. **Stack Seni Bina**:
   - FastAPI (`backend/routers/dohnut.py`) + GangNiaga WebBridge (`http://127.0.0.1:10087`) + Chrome User Profile 50 (`thisisdohnut@gmail.com`).
2. **Endpoint Aktif**:
   - `GET /api/dohnut/stats`: Metrik kewangan jualan (RM 1,420.50), pesanan pembakar, inventori doh.
   - `POST /api/dohnut/orders`: Saluran Kanban pembakar 4-tahap (Preparing, Frying, Glazing, Dispatch).
   - `POST /api/dohnut/social/generate`: Penjana kandungan promosi 6-platform masa-nyata.
   - `POST /api/dohnut/social/publish-webbridge`: Penyiaran 1-ketuk terus ke TikTok, Instagram, Threads, Facebook, X, YouTube.
   - `GET /api/dohnut/agent-swarm/status`: Pemantauan 4 nod ejen utama.
   - `POST /api/dohnut/ai-labs/launch`: Pelancar 10 Google AI Labs.
3. **Pangkalan Data Persisten**:
   - `social_autopilot.db` (SQLite simpanan draf tempatan).
4. **Pengesahan Ujian**:
   - `pytest tests/test_dohnut_api.py -v` (5/5 PASS).
   - Sut ujian regresi penuh melepasi 84/84 ujian unit.

