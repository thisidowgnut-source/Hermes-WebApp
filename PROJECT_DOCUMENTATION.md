# 🦅 Hermes OS Command Center & Telegram WebApp — Project Documentation

Dokumen ini mengandungi dokumentasi seni bina, modul antaramuka, aliran data, dan panduan lengkap bagi **Hermes OS Command Center & Telegram WebApp** (Vibe Coder Action HUD Edition).

---

## 📌 1. Ringkasan Projek (Project Overview)

**Hermes OS Command Center** adalah antaramuka kawalan ejen AI (*AI Agent Command Center / HUD*) yang direka khas untuk **Vibe Coder & System Architect**. Ia membolehkan pemantauan real-time, perlaksanaan arahan shell PTY pantas, pengurusan *multi-agent swarm*, dan kawalan *remote desktop* menerusi peranti mudah alih (Telegram Mini App) mahupun pelayar web desktop.

### 🔑 Prinsip Utama Reka Bentuk (Core Philosophy):
1. **Sifar Slop & Action-Oriented**: Membuang meter statik yang tidak berguna (seperti bulatan CPU/RAM statik) dan menggantikannya dengan **Grid Pelancar Tindakan 1-Ketuk (1-Tap Action Launchers)** dan **Bar Arahan AI Direct**.
2. **Mobile-First & Telegram Native**: Dioptimumkan khas untuk sasaran sentuhan ibu jari **48px**, disokong oleh enjin fizikal **ReactBits Elastic Inertia Scroller**, dan terintegrasi secara langsung dengan API Telegram WebApp (`tg.CloudStorage`, `tg.BackButton`, `tg.HapticFeedback`).
3. **Cyberpunk OLED Aesthetic**: Reka bentuk gelap berasaskan Pure Black (`#000000`), aksen neon purple (`#c084fc`), ikon lucide profesional, dan struktur Bento-Box tanpa skrol buruk.

---

## 🏗️ 2. Seni Bina Sistem (System Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            TELEGRAM MINI APP / MOBILE WEB                   │
│         (ReactBits Elastic Dock | Direct AI Bar | 1-Tap Launchers)          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTPS / WebSockets (trycloudflare.com)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLOUDFLARE TUNNEL ENGINE                           │
│               (cloudflare_webhook_updater.py Auto-Sync)                      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Local Reverse Proxy
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI BACKEND (Port 9230)                       │
│    ┌───────────────────┬───────────────────┬───────────────────────────┐    │
│    │  REST API Routes  │  xterm.js PTY WS  │ Telegram Webhook Router   │    │
│    └─────────┬─────────┴─────────┬─────────┴─────────────┬─────────────┘    │
└──────────────┼───────────────────┼───────────────────────┼──────────────────┘
               │                   │                       │
               ▼                   ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            LOCAL SYSTEM HARDWARE                            │
│      (PowerShell 7.4 | Process Manager | Obsidian Vault | Pytest Suite)     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 3. Katalog Modul & Sub-Sistem (All 14 Sub-Systems)

Aplikasi ini mengandungi **14 Modul Antaramuka** yang boleh diakses melalui Dock Bawah atau Modal Katalog (`#mod-appdrawer`):

### 1. 📟 Shell Terminal (`mod-terminal`)
- **Teknologi**: Xterm.js + WebSockets PTY Stream (`pwsh.exe`).
- **Ciri-Ciri**: 
  - **Mac OS Control Dots Header**: Red/Yellow/Green dot controls + status `● PTY LIVE`.
  - **1-Tap Preset Chips Toolbar**: 6 butang arahan pantas (`clear`, `ls -la`, `pytest`, `top cpu`, `git status`, `netstat`).
  - **Mobile Keypad Quick Bar**: `[CTRL+C]`, `[TAB]`, `[▲ UP]`, `[▼ DOWN]`, `[CLEAR]`.

### 2. 🌐 Browser Vision (`mod-browser`)
- **Teknologi**: Chrome DevTools Protocol + Playwright Stream.
- **Ciri-Ciri**: Paparan penstriman persekitaran pelayar *remote* secara real-time dengan mod **Take Control** untuk pengesahan visual.

### 3. 📁 File Explorer (`mod-files`)
- **Teknologi**: FastAPI Filesystem Router.
- **Ciri-Ciri**: Navigasi direktori tempatan Drive C: & Drive D: dengan kebolehan membaca dan memantau saiz fail.

### 4. 📊 Process Manager (`mod-monitor`)
- **Teknologi**: `psutil` System Diagnostics.
- **Ciri-Ciri**: Senarai proses sistem berserta PID, penggunaan memori (MB), dan butang **1-Tap Kill Process**.

### 5. 🤖 Multi-Agent Swarm (`mod-swarm`)
- **Teknologi**: Hermes Subagent Manager.
- **Ciri-Ciri**: Pemantau perlaksanaan ejen selari (*Hyper-Parallel Assembly*) dan butang **+ SPAWN** untuk melancarkan ejen baharu.

### 6. 🎙️ Voice Terminal & STEM Spectrum (`mod-audio`)
- **Teknologi**: Speech Recognition Engine + Web Audio API.
- **Ciri-Ciri**: Visualisator spektrum frekuensi audio 4-STEM (Vocals, Drums, Bass, Other) dan penukar suara-ke-arahan CLI.

### 7. 📡 Network Scanner (`mod-netscan`)
- **Teknologi**: Socket Listener & NetTCPConnection.
- **Ciri-Ciri**: Imbasan port terdedah dan penyemakan alamat IP luaran/dalaman.

### 8. 🛡️ Threat Sentinel (`mod-threat`)
- **Teknologi**: Windows Process Security Scanner.
- **Ciri-Ciri**: Pengesan imej proses luar biasa atau aplikasi tidak ditandatangani.

### 9. 🔒 FIM & Firewall (`mod-forensics`)
- **Teknologi**: SHA-256 Hash Integrity Checking.
- **Ciri-Ciri**: Pemantau integriti fail utama dan aturan Firewall Windows.

### 10. ⚙️ Cron Workflow (`mod-workflow`)
- **Teknologi**: Async DAG Task Engine & Task Scheduler.
- **Ciri-Ciri**: Pengurus tugasan berulang (*recurring tasks*) dan aliran paip automasi.

### 11. 📓 Obsidian Graph (`mod-obsgraph`)
- **Teknologi**: Obsidian Knowledge Vault Bridge.
- **Ciri-Ciri**: Visualisator rantaian *wikilinks* bagi 2,708 nota Hermes-Obsidian dan 4 MOC master hub.

### 12. 📋 Kanban Board (`mod-kanban`)
- **Teknologi**: Local Storage Task Board.
- **Ciri-Ciri**: Papan status tugasan (Backlog, In Progress, Verified, Done).

### 13. 🗂️ App Drawer (`mod-appdrawer`)
- **Teknologi**: Bento Grid Sub-System Catalog.
- **Ciri-Ciri**: Modal paparan penuh katalog 14 modul yang disusun mengikut 4 kategori utama (*Control & Shell*, *Agents & Automation*, *Security & Forensics*, *Knowledge & Tasks*).

---

## ⚡ 4. Grid Pelancar Tindakan 1-Ketuk (1-Tap Action Launchers)

Di bahagian tengah Dashboard Utama, terdapat **6 Butang Makro Impak Tinggi**:

| Butang Action | Fungsi Utama | Skrip / Executable |
| :--- | :--- | :--- |
| **🛡️ AUDIT & FIX** | Menjalankan audit kod & auto-fix lint/bugs | `executeDirectHermesCommandText(...)` |
| **▶️ RUN PYTEST** | Melancarkan ujian test suite backend | `python -m pytest tests/` |
| **💀 KILL ZOMBIES** | Membuang proses latar belakang tergantung | `scripts/cleanup_tasks.py` |
| **📖 SYNC VAULT** | Membina semula wikilinks & MOC Obsidian | `scripts/wikilink_builder.py` |
| **🤖 SPAWN SWARM** | Melancarkan unit subagent baharu secara parallel | `quickSpawnAgent()` |
| **🔗 SYNC TUNNEL** | Menyelaras Cloudflare Tunnel & Webhook Telegram | `scripts/cloudflare_webhook_updater.py` |

---

## 📱 5. Enjin Fizik Mobile-First & ReactBits Dock

Dock bawah dibina berasaskan **ReactBits 2026 Elastic Inertia Engine**:
- **Daya Inersia Fizik (`velX *= 0.92`)**: Dileret dengan kesan kelajuan *fling* semula jadi mengikut peranti perumah iOS/Android.
- **Lebar Skrol 828px**: Menampung 15 butang navigasi tanpa sebarang penyelewengan (*layout clipping*).
- **Saiz 48px Touch Target**: Menepati standard aksesibiliti sentuhan ibu jari.
- **Integrasi Telegram Native**:
  - `tg.CloudStorage.setItem('last_active_module', modId)` — Mengingati modul terakhir pengguna.
  - `tg.BackButton` — Butang fizikal kembali Telegram untuk menutup sebarang modal overlay.
  - `tg.HapticFeedback` — Getaran haptik peranti semasa butang ditekan.

---

## 🚀 6. Panduan Pembangunan & Perlaksanaan (Run Commands)

### A. Melancarkan Pelayan Backend WebApp:
```powershell
cd C:\Users\megat\Hermes-WebApp
C:\Users\megat\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe server.py
```

### B. Melancarkan Terowong Cloudflare & Automasi Webhook Telegram:
```powershell
$env:PYTHONUNBUFFERED="1"
C:\Users\megat\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe scripts\cloudflare_webhook_updater.py
```

### C. Menjalankan Ujian Empirikal Test Suite (Pytest):
```powershell
C:\Users\megat\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -m pytest tests/
```

### D. Menguji Antaramuka Menggunakan Chrome DevTools MCP:
```javascript
// Navigasi ke URL terowong live & emulasi iPhone 14
navigate_page({ url: "https://culture-libs-alternatives-increased.trycloudflare.com/" });
emulate({ viewport: "390x844x3,mobile,touch" });

// Jalankan ujian modul programatik
evaluate_script({ function: "() => { openModule('terminal'); return document.getElementById('mod-terminal').classList.contains('active'); }" });
```

---

## 📄 7. Lokasi Fail Utama (File Map)

- **Antaramuka Utama (Single Page App)**: `C:\Users\megat\Hermes-WebApp\static\index.html`
- **Pelayan FastAPI Backend**: `C:\Users\megat\Hermes-WebApp\server.py`
- **Skrip Automasi Tunnel & Webhook**: `C:\Users\megat\Hermes-WebApp\scripts\cloudflare_webhook_updater.py`
- **Skrip Pembersihan Zombie Process**: `C:\Users\megat\Hermes-WebApp\scripts\cleanup_tasks.py`
- **Dokumentasi Projek Ini**: `C:\Users\megat\Hermes-WebApp\PROJECT_DOCUMENTATION.md`
- **Memori Ruang Kerja (Global Workspace)**: `C:\GEMINI.md`

---
*Dokumen ini dijana secara autonomi oleh Antigravity Hyper-Sovereign Conductor pada 27 Julai 2026.*
