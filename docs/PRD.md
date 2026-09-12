---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — Product Requirements Document (PRD)"
document_id: "HERMES-WEBAPP-PRD-001"
version: "3.5.0"
last_updated: "2026-09-12 15:22:00 MYT"
maintainer: "GangBo Sovereign Architect"
classification: "MISSION-CRITICAL // SOVEREIGN ENGINE"
lifecycle_status: "PRODUCTION / STABLE"
---

# 📋 Product Requirements Document (PRD) — Hermes OS & Doh-Nut Sovereign Mission Control

> **Executive Product Blueprint for an ultra-low latency Telegram Mini App & Progressive Web App (PWA) delivering unstoppable remote PC orchestration, live browser automation, multi-agent telemetry, and All-in-1 mission control for Doh-Nut (`thisisdohnut@gmail.com`).**

---

## 📜 Audit & Revision Ledger

| Version | Timestamp (MYT / ISO) | Author / Agent | Root Cause / User Intent | Scope & Components Touched | Empirical Validation Proof |
|:---|:---|:---|:---|:---|:---|
| **`3.5.0`** | 2026-09-12 15:22:00<br>`2026-09-12T07:22:00Z` | Antigravity Conductor | Penyatuan All-in-1 Mission Control Doh-Nut ke dalam Hermes-WebApp tanpa mengganggu Telegram Menu Button. | `backend/routers/dohnut.py`, `static/index.html`, `docs/PRD.md` | 5/5 API Endpoints 200 OK, Chrome DevTools MCP Desktop & Mobile (390px) verified. |
| **`3.0.0`** | 2026-07-27 18:00:00<br>`2026-07-27T10:00:00Z` | Hermes Dev Squad | Reka bentuk semula Bento-Box Dashboard, pembetulan CSS overlay z-index, integrasi Termux Hacker's Keyboard. | `static/index.html`, `backend/websockets/terminal.py` | 84/84 Pytest suite passed, 14 modul UI lulus ujian headless DOM. |
| **`1.0.0`** | 2026-07-20 12:00:00<br>`2026-07-20T04:00:00Z` | Megat / Bo | Spesifikasi asal Hermes OS Telegram WebApp. | Core FastAPI + WebSockets + Cloudflare Tunnel | PWA & Telegram WebApp MVP. |

---

## 1. Executive Summary & Vision

### 1.1 Product Overview
**Hermes OS & Doh-Nut Sovereign Mission Control** ialah pusat kawalan berautonomi tinggi berasaskan WebApp yang berjalan pada pelayan hos tempatan (`127.0.0.1:9220`) dan boleh diakses di mana-mana sahaja di dunia melalui **Telegram Mini App** atau pelayar desktop moden (PWA).

Aplikasi ini menamatkan batasan bot Telegram konvensional (had mesej teks 4096 aksara, tiada interaktiviti visual kompleks) dengan menyediakan persekitaran skrin penuh 16 modul yang menggabungkan:
1. **Kawalan PC Jarak Jauh Tanpa Had**: Terminal PowerShell ConPTY berkuasa penuh, pelayar Playwright Chromium dengan kawalan klik & taip langsung, penjelajah fail, dan pengurus proses.
2. **All-in-1 Doh-Nut Sovereign HQ**: Pengurusan operasi jualan bakeri harian, Kanban saluran pembakar 4-tahap, pesanan katering korporat, penjana promosi viral 6-platform (TikTok, IG, Threads, FB, X, YouTube), telemetri skuad ejen AI, dan 10 pelancar pantas Google AI Labs.
3. **Pengekalan Terowong Cloudflare Kalis-Ranap**: Integrasi berterusan dengan Telegram Chat Menu Button (`Open Hermes OS`) tanpa gangguan pengesahan captcha atau skrin amaran pihak ketiga.

### 1.2 Sasaran Pengguna (Target Audience)
- **Sovereign System Operators & Architects**: Pengendali sistem yang memerlukan kawalan terminal dan pemantauan perkakasan PC hos dari telefon pintar.
- **Doh-Nut Business Operations**: Pengurus kedai roti/donut yang memantau jualan masa-nyata, saluran pembakar dapur, dan penyiaran kempen media sosial tanpa membuka pelbagai aplikasi berasingan.
- **Autonomous AI Swarms**: Ejen-ejen pintar (Hermes Conductor, Antigravity, Open Design, WebBridge) yang memerlukan saluran intervensi manusia (Human-in-the-Loop) untuk kelulusan tugasan kritikal.

---

## 2. Problem Statement & Market Opportunity

| Isu Konvensional | Impak Negatif | Penyelesaian Hermes OS & Doh-Nut HQ |
|:---|:---|:---|
| **Kelemahan RDP / VNC Biasa** | Sangat lambat pada peranti bimbit, memakan lebar jalur besar, dan sukar digunakan dengan kawalan sentuh kecil. | Antaramuka berasaskan WebSocket ringan dengan kanvas xterm.js dan penstriman bingkai JPEG/WebP termampat. |
| **Fragmentasi Alatan Doh-Nut** | Pengendali terpaksa membuka berasingan: POS/invois, aplikasi TikTok/IG, terminal PC, dan tab pelayar Chrome. | Penyatuan `#mod-dohnut` merangkumi metrik jualan, kanban dapur, penjana viral 6-platform, dan 10 makmal AI. |
| **Isu Sekatan Terowong (Interstitial Warning)** | Servis seperti Localtunnel atau ngrok percuma memaparkan skrin amaran "Click to Continue" yang merosakkan Telegram Mini App. | Cloudflare Tunnels passthrough terus dengan SSL termination telus dan automasi `setChatMenuButton`. |
| **Halangan Captcha Ejen AI** | Ejen autonomi terkandas apabila menghadapi pengesahan 2FA, Captcha, atau borang sensitif. | Protokol HITL memaparkan modal intervensi visual pada Telegram untuk diselesaikan pengguna dalam beberapa saat. |

---

## 3. Core Product Goals & Success Metrics

### 3.1 Matlamat Produk (Key Objectives)
- **Zero-Latency Response**: Peralihan antaramuka dan tindanan modul bawah 150ms; latensi WebSocket terminal bawah 50ms.
- **Zero-Disruption Telegram Tunneling**: Pengguna boleh membuka WebApp bila-bila masa melalui Chat Menu Button Telegram tanpa perlu mengkonfigurasi semula URL.
- **Anti-AI Slop Aesthetic**: Pematuhan mutlak standard reka bentuk OLED Neo-Brutalism (Pure Black `#000000`, 1px borders, Lucide SVGs, tabular-nums).
- **Single Source of Truth**: Data jualan, stok, akaun media sosial, dan status swarm disegerakkan antara pangkalan data lokal, GangNiaga WebBridge, dan Obsidian Vault.

### 3.2 Metrik Kejayaan (Success Metrics)
- **API Availability**: 100% endpoint `/api/dohnut/*` dan `/api/*` mengembalikan status HTTP 200 OK.
- **Console Hygiene**: 0 ralat JavaScript (`0 errors`) pada pelayar Chrome/Telegram WebView.
- **Mobile Viewport Compliance**: 100% susun atur muat pada skrin mudah alih 390px x 844px tanpa limpahan mendatar (*zero horizontal scroll*).
- **Social Dispatch Latency**: <1.0 saat untuk menyuntik draf promosi ke tab aktif Chrome Profile 50 via WebBridge.

---

## 4. Functional Requirements & Module Specifications

### 4.1 Doh-Nut Sovereign Mission Control (`#mod-dohnut`)
- **REQ-DOH-01: Financial & Order Telemetry**:
  - Memaparkan hasil jualan harian (Today's Revenue dalam format `RM 1,420.50`).
  - Memaparkan bilangan pesanan aktif (Active Baking Orders) dan pesanan selesai.
  - Memaparkan barisan tempahan katering korporat (Catering Queue: 150 Pax).
  - Memaparkan baki adunan doh sedia goreng (Dough Batches Left).
- **REQ-DOH-02: 4-Stage Baking & Glazing Kanban**:
  - Saluran 1: *Preparing* (Uli dan peram doh).
  - Saluran 2: *Deep Frying* (Goreng suhu 175°C keemasan).
  - Saluran 3: *Glazing* (Salutan frosting pink, lelehan matcha, taburan gula).
  - Saluran 4: *Ready / Dispatch* (Kotak pembungkusan sedia untuk Lalamove/Grab).
  - Butang `Sync` untuk kemaskini status secara masa-nyata.
- **REQ-DOH-03: Live Signature Stock Tracking**:
  - Penjejakan stok perisa Kuih Burger Malaysia, Sira Kuih Keria, Sira Sambal, Classic Glazed, dan Matcha White Choco (dengan penunjuk amaran LOW STOCK).
- **REQ-DOH-04: Omnichannel 6-Platform Social Generator**:
  - Input topik promosi 1-baris.
  - Penjanaan draf serentak berformat khusus untuk TikTok (`@thisisdohnut`), Instagram Reels, Threads, Facebook, X, dan YouTube Shorts.
  - Butang `1-TAP POST` bagi setiap platform untuk menyiarkan teks secara automatik via WebBridge ke Chrome Profile 50.
- **REQ-DOH-05: Agent Swarm Telemetry**:
  - Memaparkan penunjuk status ONLINE bagi Hermes Conductor, Antigravity Conductor, GangNiaga WebBridge, dan Open Design Daemon.
  - Butang pintas: `RUN BUN 62/62`, `SYNC VAULT`, dan `KILL ZOMBIE PORTS`.
- **REQ-DOH-06: 10 Google AI Labs Launchers**:
  - Direktori 1-ketuk untuk melancarkan dan memfokuskan tetingkap pelayar ke Mixboard, Stitch, Putty, Jules, Opal, AI Studio, NotebookLM, Flow, ChatGPT, dan Labs Hub.

### 4.2 Terminal Subsystem (`#mod-terminal`)
- **REQ-TRM-01**: Sesi interaktif penuh PowerShell 7 (`pwsh.exe`) dipancarkan melalui xterm.js.
- **REQ-TRM-02**: Penapisan ketat rentetan ping WebSocket PTY bagi memastikan kanvas bebas daripada teks sampah.
- **REQ-TRM-03**: Baris Kekunci Termux Hacker's Keyboard dengan butang pantas (`ESC`, `TAB`, `CTRL+C`, `CTRL+Z`, `CTRL+L`, `|`, `/`, `-`, `~`, `\`, `&`, `>`, `$`, `*`, `"`).
- **REQ-TRM-04**: Pelarasan saiz dinamik (*responsive resize*) mengikut lebar dan tinggi skrin peranti.

### 4.3 Browser Vision Subsystem (`#mod-browser`)
- **REQ-BRW-01**: Penstriman bingkai Playwright Chromium pada kualiti tinggi termampat.
- **REQ-BRW-02**: Bar alatan pintas URL 1-ketuk (Google, GitHub, Hermes API, Ollama API).
- **REQ-BRW-03**: Sokongan interaksi sentuh (`touchstart`, `click`) dan pemetaan koordinat (X,Y) tepat ke kursor pelayar hos.
- **REQ-BRW-04**: Penunjuk neon terapung `● MANUAL CONTROL ACTIVE` tanpa menutupi gambaran web.

### 4.4 Multi-Agent Swarm, Telemetry & Security
- **REQ-SWM-01**: Senarai ejen AI yang aktif, penggunaan CPU dan RAM per ejen.
- **REQ-SEC-01**: Pengimbas integriti fail (FIM) berasaskan baseline SHA-256.
- **REQ-SEC-02**: Pengesan ancaman heuristik dan pengurusan sekatan firewall Windows (`netsh`).
- **REQ-SYS-01**: Makro pantas: `clean_temp`, `lock_pc`, `cleanup_zombies`, `sync_webhook`.

---

## 5. Non-Functional & Technical Constraints

### 5.1 Keselamatan (Zero-Trust Security)
- **Local Host Execution Only**: Pelayan dijalankan secara eksklusif pada `127.0.0.1:9220` hos Windows. Dilarang menggunakan perkhidmatan awam tanpa penyulitan hujung-ke-hujung.
- **Perlindungan Fail Sensitif**: Laluan `.env`, `.git`, dan folder rahsia disekat sepenuhnya daripada bacaan terbuka API.
- **Split-Token Architecture**: Token Telegram bot WebApp hanya digunakan untuk mesej keluar (Outbound), mengelakkan konflik HTTP 409 dengan gateway utama.

### 5.2 Pengalaman Pengguna Mudah Alih (Mobile-First Constraints)
- **100vh Lock & No Scroll**: Paparan papan pemuka utama dikunci pada `100vh` dengan `overflow: hidden` bagi mengelakkan pertembungan leretan (*swipe gesture conflicts*) di Telegram.
- **Popstate & Back Button**: Menekan butang kembali fizikal telefon atau leretan tepi menutup modal tindanan secara semula jadi menggunakan `window.onpopstate`.
- **Safe Area Insets**: Mematuhi sepenuhnya `--tg-viewport-height` dan pembolehubah kawasan selamat Telegram.

---

## 6. Release Criteria & Quality Gates

1. **Empirical Code Validation**: Setiap perubahan melepasi ujian `pytest` (0 failures).
2. **Visual Verification**: Pengesahan paparan visual melalui Chrome DevTools MCP pada kedua-dua resolusi Desktop dan Mobile (390px iPhone standard).
3. **Tunnel Stability**: Pautan `setChatMenuButton` disahkan aktif dan membuka WebApp dalam masa bawah 2 saat.
