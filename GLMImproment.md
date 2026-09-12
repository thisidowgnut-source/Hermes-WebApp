---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — GLM Improvement Plan (Struktur Projek & Backlog Kualiti)"
document_id: "HERMES-WEBAPP-GLM-IMP-001"
version: "1.0.0"
last_updated: "2026-09-12 15:45:42 MYT"
maintainer: "GangBo Sovereign Architect"
classification: "IMPROVEMENT PLAN // RESEARCH-VALIDATED"
lifecycle_status: "READY FOR EXECUTION"
---

# 🗂️ GLM Improvement Plan — Hermes-WebApp

> **Pelan pembaikan lengkap yang telah disahkan melalui deep research terhadap 6 piawaian industri: reorganisasi struktur projek (FHS 3.0 + 12-Factor App + FastAPI official template) dan backlog pembaikan dokumen/kod (F-01 hingga F-20) yang dikesan melalui review empirikal terhadap kod sebenar.**

---

## 📜 Audit & Revision Ledger

| Version | Timestamp (MYT / ISO) | Author / Agent | Root Cause / Rationale | Scope | Empirical Validation Proof |
|:---|:---|:---|:---|:---|:---|
| **`1.0.0`** | 2026-09-12 15:45:42<br>`2026-09-12T07:45:42Z` | GLM Conductor (z-ai/glm-5.3-flash) | Penyimpanan pelan improvement yang disahkan deep research — reorganisasi FHS 3.0 + backlog F-01..F-20. | Dokumen ini | 6 sumber piawaian HTTP 200; 12 pemeriksaan kod ground truth; audit 48+ fail root. |

---

## 🎯 Tujuan Dokumen

Dokumen ini ialah **single source of truth** untuk dua inisiatif pembaikan Hermes-WebApp:

1. **Bahagian A — Reorganisasi Struktur Projek**: Cadangan yang telah disahkan terhadap 6 piawaian (termasuk 2 pembetulan struktur yang dikenakan oleh research).
2. **Bahagian B — Backlog Pembaikan**: 20 penemuan (F-01..F-20) dari review teliti kod & dokumen, diutamakan mengikut risiko.

**Status**: Cadangan disahkan, **belum dilaksanakan**. Setiap FASA mesti dilaksanakan mengikut urutan dengan commit atomic.

---

# 📚 BAHAGIAN A — Reorganisasi Struktur Projek (v2, Research-Validated)

## A1. Keputusan Keseluruhan

Cadangan v1 **7/7 elemen teras disahkan** oleh piawaian; deep research memaksa **2 pembetulan struktur** (db → `var\lib`, pid → `var\run`) dan **1 pembetulan kaedah** (log ditadbir di launch config, bukan kod). Versi v2 kini melebihi piawaian, bukan sekadar memenuhinya.

## A2. Sumber Piawaian Yang Dirujuk (Semua Disahkan HTTP 200)

| Sumber | Apa Yang Disemak | Kesimpulan Untuk Projek |
|:---|:---|:---|
| [12-Factor App — Factor XI: Logs](https://12factor.net/logs) | Rawatan log sebagai event stream | App tulis ke `stdout`; environment yang menguruskan destinasian fail log |
| [12-Factor App — Factor III: Config](https://12factor.net/config) | Pemisahan config dari kod | *"Apps sometimes store config as constants in the code. This is a violation of twelve-factor"* — kunci hardcoded dilarang |
| [FastAPI Official Full-Stack Template](https://github.com/tiangolo/full-stack-fastapi-template) | Layout rasmi aplikasi FastAPI | `backend/` + `backend/README.md` + `.env` di root + pytest — layout aplikasi rasmi |
| [PyPA sampleproject](https://github.com/pypa/sampleproject) | src/ layout vs application layout | `src/` layout adalah untuk *pakej distributable* (pyproject.toml), bukan aplikasi |
| [FHS 3.0 (Filesystem Hierarchy Standard)](https://en.wikipedia.org/wiki/Filesystem_Hierarchy_Standard) | Takrif `/var/log`, `/var/lib`, `/var/run`, `/var/spool` | `var/lib` = database/state; `var/run` = pid; `var/log` = log; `var/spool` = queue |
| [Divio Documentation System](https://docs.divio.com/) | Taksonomi 4 kuadran dokumentasi | Tutorial / How-to / Reference / Explanation |

## A3. Audit Keadaan Semasa (Bukti Empirikal)

```
DIAGNOSIS STRUKTUR SEMASA (dari survey sebenar, 2026-09-12):
┌──────────────────────────────────────────────────────────────────┐
│ 🔴 P0  .git TIADA          → 33+ fail kod & docs TANPA version   │
│                            →  control. Satu salah padam = hilang │
│ 🔴 P0  Log ditanam di root →  server.log 9.6MB, watchdog.log     │
│                            →  1.3MB, tunnel_keeper.log 1MB,      │
│                            →  8+ log lain di ROOT                │
│ 🟠 P1  Root penuh dokumen  →  12+ .md bersejarah bercampur       │
│                            →  dengan fail aktif                  │
│ 🟠 P1  scripts/40 fail     →  patches + ops + debug + .bak +     │
│                            →  PNG/HTML output bercampur          │
│ 🟠 P1  Paket MCP di root   →  6 fail MCP install/docs di root    │
│ 🟡 P2  Junk & duplikat     →  CUsersmegat...verify-fix.py,       │
│                            →  .pytest_cache2/tmp2, .bak files,   │
│                            →  index_improved.html                │
│ 🟡 P2  logs/ KOSONG        →  folder ada, tapi log semua di root │
│    DB & runtime data       →  social_autopilot.db + .queue/*.json │
│                            →  di root (runtime data + kod campur)│
└──────────────────────────────────────────────────────────────────┘
```

## A4. Matriks Pengesahan: Cadangan vs Piawaian

| # | Elemen | Piawaian Yang Menyokong | Verdict |
|:---:|:---|:---|:---:|
| V1 | Kekalkan layout `backend\` (TIADA `src\`) | FastAPI official template guna `backend/`; PyPA `src/` layout untuk pakej distributable sahaja | ✅ |
| V2 | `.env` di root + gitignored | FastAPI template "`.env` configuration" di root; 12-Factor III config per-deploy | ✅ |
| V3 | Kunci API TIDAK hardcoded | 12-Factor III verbatim: *"store config as constants in the code... violation of twelve-factor"* + litmus test open-source | ✅ |
| V4 | `tests\` + pytest di root | FastAPI template: "✅ Tests with Pytest" | ✅ |
| V5 | `git init` + baseline commit sebelum migrasi | Conventional Commits (mandat AGENTS.md) | ✅ |
| V6 | `docs\` berpusat dengan arkib | Divio 4 kuadran | ✅ |
| V7 | Folder `var\` untuk runtime data | FHS 3.0: `/var` = *"Variable files... continually change during normal operation"* | ✅ |

## A5. Pembetulan Yang Dikenakan Oleh Research

### CORRECTION A — Log: Kaedah Lebih Penting Daripada Lokasi ([12-Factor XI](https://12factor.net/logs))

Piawaian secara literal: *"A twelve-factor app never concerns itself with routing or storage of its output stream. It should not attempt to write to or manage logfiles. Instead, each running process writes its event stream, unbuffered, to `stdout`."*

- **App** (`backend`): kekal tulis ke `stdout` (sudah betul — `observability.py` guna `stream=sys.stdout`; `LOG_FILE` env ialah pilihan environment)
- **Environment** (launch config): yang memutuskan destinasian. `server.log`, `watchdog.log`, `tunnel_keeper.log` di root wujud kerana skrip luar diarahkan tulis ke root.
- **Pembetulan**: arahkan semula destinasian dalam **launch config** (`deploy\hermes_startup.vbs`, task scheduler, arahan manual) ke `var\log\` — BUKAN ubah kod skrip.

### CORRECTION B — Subfolder `var\` Ikut FHS 3.0

| Item | Cadangan v1 (SALAH) | FHS 3.0 | Pembetulan v2 |
|:---|:---|:---|:---|
| `social_autopilot.db` | ❌ `var\db\` | `/var/lib` = *"State information. Persistent data modified by programs as they run (e.g., databases)"* | ✅ → **`var\lib\`** |
| `server.pid`, `tunnel_keeper.pid` | ❌ `var\log\` | `/run` = *"Run-time variable data... removed or truncated at the beginning of the boot process"* | ✅ → **`var\run\`** |
| `.queue\` (queue.json) | Kekal | `/var/spool` = *"Spool for tasks waiting to be processed"* | 🟡 Konsep = **spool**; kekal di root buat sementara (hardcoded `system.py:14`), FASA 2 opsyenal → `var\spool\` |

### CONFIRMATION C — Layout `src\` DITOLAK

PyPA `src/` layout untuk pakej yang diedarkan ke PyPI; FastAPI official template (aplikasi) guna `backend/` flat. Hermes-WebApp ialah aplikasi self-hosted → `backend\` adalah standard yang betul.

### CONFIRMATION D — Organisasi `docs\` Ikut Divio 4 Kuadran

| Kuadran Divio | Fail | Nota |
|:---|:---|:---|
| **Tutorial** | README.md (Master Guide) | Orientasi pemula |
| **How-to guides** | DEPLOYMENT.md, TROUBLESHOOTING.md | Resipi langkah demi langkah |
| **Reference** | API.md, ARCHITECTURE.md, DESIGNS.md | Fakta teknikal |
| **Explanation** | PRD.md, AGENTS.md, SKILLS.md | Konteks & latar belakang |
| *(sejarah)* | archive\ | Bukan kuadran — kekal berasingan |

Tambah: `docs\README.md` indeks yang memetakan setiap fail ke kuadran.

## A6. Struktur Sasaran (v2)

```
C:\Users\megat\Hermes-WebApp\
├── .git\                          # [BAHARU] git init — FASA 0, WAJIB
├── .env                           # 🔒 KEKAL di root (config.py:6 muat dari sini)
├── .env.example
├── .gitignore                     # Dikemaskini (lihat A10)
├── main.py                        # 🔒 KEKAL (entry point, dirujuk deploy/)
├── conftest.py                    # 🔒 KEKAL (pytest rootdir)
├── pytest.ini                     # 🔒 KEKAL (pytest rootdir)
├── requirements.txt
├── README.md                      # Master Guide
├── CHANGELOG.md
│
├── backend\                       # 🔒 KOD PRODUKSI — tak diubah
│   ├── main.py  config.py  auth.py  bot_bridge.py  observability.py
│   ├── routers\  services\  websockets\
│
├── static\                        # 🔒 KEKAL (config.py:21 STATIC_DIR)
│   ├── index.html  manifest.json  icons\
│
├── tests\                         # 11 fail ujian
├── deploy\                        # 🔒 KEKAL (dirujuk .vbs/.service)
│
├── docs\                          # 📁 SEMUA dokumentasi — Divio 4 kuadran
│   ├── README.md                  # [BAHARU] indeks kuadran
│   ├── PRD.md  ARCHITECTURE.md  AGENTS.md  API.md  SECURITY.md
│   ├── DEPLOYMENT.md  DESIGNS.md  SKILLS.md  TROUBLESHOOTING.md
│   ├── TEST_INFRA.md              # ⬅ pindah dari root
│   ├── n8n\                       # ⬅ 6 JSON workflow
│   ├── archive\                   # ⬅ dokumen bersejarah (dari root)
│   │   ├── reviews\               #    4 fail REVIEW + DSH_REVIEW
│   │   ├── planning\              #    PROJECT, PROJECT_DOCUMENTATION,
│   │   │                          #    IMPROVEMENT_PLAN, TODO,
│   │   │                          #    ORIGINAL_REQUEST, BRIEFING, handoff
│   │   └── patches\               #    index_improved.html, .bak files
│   └── superpowers\               # KEKAL (plans/specs/sdd)
│
├── scripts\                       # 🧹 DIKATEGORIKAN (lihat A7)
│   ├── ops\  telegram\  patches\  automation\  debug\
│
├── tools\                         # 🔧 Alat pembangunan (bukan runtime)
│   └── mcp\                       # ⬅ 6 fail MCP dari root
│
└── var\                           # 📊 RUNTIME DATA — gitignored (FHS 3.0)
    ├── log\                       # ⬅ 11 log dari root
    ├── lib\                       # ⬅ social_autopilot.db [FASA 2 — edit kod]
    ├── run\                       # ⬅ *.pid
    └── spool\                     # ⬅ .queue\ [FASA 2 opsyenal — edit kod]
```

## A7. Pemetaan Migrasi `scripts\` (40 fail → 5 subfolder)

| Subfolder | Fail | Alasan |
|:---|:---|:---|
| `scripts\ops\` | hermes_watchdog.py, tunnel_keeper.py, cleanup_tasks.py, queue_manager.py, zombie_slayer.ps1, defender_exclusions.ps1, keeper_task.cmd, cloudflare_webhook_updater.py | Operasi hos/daemon |
| `scripts\telegram\` | setup_telegram_menu.py, fix_tg.py, update_telegram_url.py, fix_terminal_id.py, aiogram_bridge.py, n8n_telegram_hitl.py | Integrasi Telegram |
| `scripts\patches\` | apply_*.py (7 fail), revert_ugly_patches.py, remove_jitter.py, generate_icons.py, encrypt_config.py | Transformasi UI/konfig |
| `scripts\automation\` | automate_fb.py, fb-automation.js, extract_cookies.py, decrypt_cookies.py, find-first-photo.js, test-connect.js | Automasi pelayar/sosial |
| `scripts\debug\` | debug_ui.py, debug_facebook.png, fb_public.html | Artefak debugging |
| `docs\archive\patches\` | hermes_watchdog.py.bak_20260826_195623, tunnel_keeper.py.bak_20260826_195623 | Sandaran bersejarah |
| **PADAM** | `__init__.py` di scripts/ (tiada import paket — sahkan dulu) | Kemungkinan lapuk |

## A8. 🔒 Kekangan: Apa Yang TIDAK BOLEH Digerakkan

| Item | Kenapa Kekal | Bukti |
|:---|:---|:---|
| `.env` di root | `load_dotenv(BASE_DIR/.env)` | `config.py:6` |
| `static\` di root | `STATIC_DIR = BASE_DIR/static` | `config.py:21` |
| `main.py` di root | Entry point; dirujuk deploy/ + uvicorn | `main.py:4` |
| `conftest.py` + `pytest.ini` di root | pytest rootdir discovery | konvensyen pytest |
| `.queue\` di root *(sementara)* | `QUEUE_FILE = BASE_DIR/.queue/queue.json` | `system.py:14` |
| `social_autopilot.db` di root *(sementara)* | `DB_PATH = BASE_DIR/social_autopilot.db` | `dohnut.py:35` |
| `backend\`, `deploy\`, `tests\` | Struktur sudah betul + dirujuk merentas | — |
| Proses berjalan | AGENTS §3.1: jangan ganggu cloudflared / port 9220 semasa migrasi | `docs/AGENTS.md` 3.1 |

## A9. Pelan Pelaksanaan Berperingkat

**FASA 0 — Version Control (WAJIB DULU, 5 minit)**
```powershell
git init
git add -A
git commit -m "chore: baseline sebelum restrukturisasi projek"
```
> ⚠️ Sebelum `git add -A`: pastikan `.gitignore` sedia (lihat A10) supaya `.env` TIDAK ter-commit.

**FASA 1 — Pembersihan Sifar-Risiko (tiada edit kod, ~15 minit)**
```powershell
# 1. Padam junk
Remove-Item "CUsersmegatAppDataLocalTemphermes-verify-fix.py" -Force
Remove-Item .pytest_cache2, .pytest_tmp2 -Recurse -Force -ErrorAction SilentlyContinue

# 2. Bina struktur baharu
New-Item -ItemType Directory -Force -Path var\log, var\lib, var\run, var\spool,
  tools\mcp, docs\archive\reviews, docs\archive\planning, docs\archive\patches,
  docs\n8n, scripts\ops, scripts\telegram, scripts\patches,
  scripts\automation, scripts\debug

# 3. Pindah log dari root → var\log (12-Factor XI: destinasian tangkapan env)
Move-Item server.log, server_err.txt, server_log.txt, main.log,
  cloudflare*.log, cloudflared*.log, tunnel_keeper.log, watchdog.log var\log\

# 4. Pindah pid → var\run (FHS: /run)
Move-Item server.pid, tunnel_keeper.pid var\run\

# 5. Arkib dokumen bersejarah
Move-Item *REVIEW*.md, DSH_REVIEW_V4.md docs\archive\reviews\
Move-Item PROJECT.md, PROJECT_DOCUMENTATION.md, IMPROVEMENT_PLAN.md,
  TODO.md, ORIGINAL_REQUEST.md, BRIEFING.md, handoff.md, TEST_INFRA.md docs\archive\planning\

# 6. Paket MCP → tools\mcp\
Move-Item install-mcp-servers.*, test-mcp-servers.sh, Test-MCPServers.ps1,
  MCP-Servers-CONFIG.json, README-MCP-*.md tools\mcp\

# 7. N8n workflow JSON
Move-Item docs\n8n_*.json docs\n8n\

# 8. Artefak dev
Move-Item static\index_improved.html docs\archive\patches\

git commit -m "chore: reorganize root (logs→var/log, pid→var/run, docs archive, tools/mcp)"
```

**FASA 2 — Pindahan DB (perlu 1 edit kod + ujian)**
```python
# dohnut.py:35 — dari:
DB_PATH = os.path.join(config.BASE_DIR, "social_autopilot.db")
# kepada:
DB_PATH = os.path.join(config.BASE_DIR, "var", "lib", "social_autopilot.db")
```
```powershell
Move-Item social_autopilot.db var\lib\
pytest tests/test_swarm_api.py   # pengesahan
```
```powershell
git commit -m "refactor: relocate runtime db to var/lib (FHS 3.0)"
```
> Opsyenal FASA 2b: `.queue\` → `var\spool\` (edit `system.py:14` QUEUE_FILE + `config.py`).

**FASA 3 — Pembetulan Destinasian Log Dalam Launch Config (12-Factor XI)**
- Edit `deploy\hermes_startup.vbs` + arahan manual/task scheduler supaya output watchdog/tunnel_keeper/server pergi ke `var\log\`
- BUKAN ubah kod skrip — app kekal tulis ke stdout; environment menguruskan routing
```powershell
git commit -m "chore: route daemon logs to var/log via launch config (12-factor)"
```

**FASA 4 — Subfolder scripts\ + commit pengesahan akhir**
```powershell
# Ikut pemetaan A7, kemudian:
pytest           # sahkan tiada keputusan pecah
git commit -m "refactor: categorize scripts into ops/telegram/patches/automation/debug"
```

## A10. `.gitignore` Dikemaskini (Cadangan Penuh)

```gitignore
# Runtime data — JANGAN commit (FHS 3.0)
var/
*.log
*.pid
social_autopilot.db
.queue/

# Cache & artifacts
__pycache__/
.pytest_cache*/
.pytest_tmp*/
*.pyc

# Secrets (12-Factor III)
.env

# OS / editor
Thumbs.db
desktop.ini
```

## A11. Polisi Higien Berterusan

1. **Log hanya ke `var\log\`** — dianjurkan di launch config, bukan di root
2. **Dokumen aktif di `docs\`**; yang mati → `docs\archive\` (jangan biar bersejarah di root lagi)
3. **Skrip baharu** mesti masuk subfolder `scripts\` yang betul dari hari pertama
4. **Commit atomic** per perubahan logik — Conventional Commits
5. **`.bak` dilarang** — guna `git` sebagai sandaran
6. **Kekangan AGENTS §3.1**: jangan ganggu cloudflared / port 9220 semasa migrasi

## A12. Ringkasan Impak

| Metrik | Sebelum | Selepas |
|:---|:---:|:---:|
| Fail di root | **48+** | **~8** |
| Version control | ❌ Tiada | ✅ Git + baseline |
| Log terbesar di root | 9.6 MB | 0 (var\log) |
| Dokumen bersejarah di root | 12 | 0 (docs\archive) |
| Skrip tanpa kategori | 40 bercampur | 5 subfolder jelas |

---

# 🐛 BAHAGIAN B — Backlog Pembaikan Dokumen & Kod (F-01..F-20)

Dikesan melalui review teliti 5 fail .md "sources of truth" (PRD, ARCHITECTURE, AGENTS, README, LOG-GANGBO) disahkan terhadap kod sebenar.

## 🔴 P0 — Kritikal (Sebelum Dokumen Dipanggil "Source of Truth")

| ID | Penemuan | Bukti | Tindakan |
|:---:|:---|:---|:---|
| F-01 | **Dakwaan keselamatan PALSU** — README/PRD/ARCHITECTURE mendakwa whitelist `.env`/`.git` + traversal guard dalam `/api/files`; grep 853 baris `system.py` = **0 padanan**. Kod hanya semak existence + 2MB | `system.py:426-473` | Pilih: (A) tambah whitelist + traversal guard dalam kod, ATAU (B) tukar 3 ayat dokumen kepada realiti + ledger *known gap* |
| F-02 | **Kunci API WebBridge hardcoded** — pelanggaran 12-Factor III | `dohnut.py:30` `WEBBRIDGE_KEY = "8b0494ab..."` | Alih ke `.env`: `WEBBRIDGE_KEY = os.getenv("WEBBRIDGE_KEY", "")` |
| F-03 | **Kod sampel ARCHITECTURE §2.2 salah 5/5 elemen** — doc: `httpx.AsyncClient`, `/action/inject`, `X-API-Key`, payload inject; kod sebenar: `urllib.request`, `/health`→`/command`, `Authorization: Bearer`, payload navigate sahaja | `dohnut.py:195-244` | Ganti sampel dengan kod sebenar |
| F-04 | **"5/5 API Endpoints" vs 7 sebenar** — dohnut.py ada 7 endpoint; keempat-empat ledger kata 5/5 | `dohnut.py` | Tukar → "7/7" atau nyatakan skop |

## 🟠 P1 — Utama (Minggu Ini)

| ID | Penemuan | Bukti | Tindakan |
|:---:|:---|:---|:---|
| F-05 | README runbook rujuk `tests/test_dohnut_api.py` — **fail tidak wujud** (11 test lain ada); tiada ujian router dohnut langsung | `README.md:333`; `tests/` survey | Bina fail ujian itu (disyorkan) atau buang rujukan |
| F-06 | README tree salah 2 kandungan: PySide6 (tiada dalam requirements) + `scripts/ai_labs_dispatcher.py` (sebenar di `C:\Users\megat\Scripts\`, luar repo) | `requirements.txt`; `dohnut.py:31` | Betulkan tree |
| F-07 | "16 modul" vs 17 sebenar — `index.html` ada 17 overlay; modul `monitor` tiada dalam katalog | `index.html` | Kira semula atau dokumen `monitor` |
| F-08 | Dakwaan ConPTY/WinPTY + "resize" — kod guna pipes biasa (`asyncio.create_subprocess_exec`); tiada pywinpty; tiada resize handler | `terminal.py:10-16` | Tukar → "async subprocess pipes"; buang/implement resize |

## 🟡 P2 — Sederhana & Kecil (Bulan Ini)

| ID | Penemuan | Bukti | Tindakan |
|:---:|:---|:---|:---|
| F-09 | Status swarm hardcoded "ONLINE 🟢" + dead code (`hermes_active`/`agy_active` dikira tapi tidak digunakan) | `dohnut.py:269-305` | Guna status dikira; buang dead code |
| F-10 | Dakwaan port 7456 (Open Design) tiada dalam kod; contoh respons ai-labs/status tidak sepadan | `dohnut.py` | Betulkan doc |
| F-11 | LOG-GANGBO kronologi pecah — entri atas ada masa, seksyen bawah tiada | `LOG-GANGBO.md` baris 11-38 vs 113+ | Seragamkan format |
| F-12 | LOG-GANGBO kandungan diduplikasi (header disalin verbatim ke Action) | baris 28-30, 34-36 | Buang duplikasi |
| F-13 | Percanggahan versi GEMINI.md: v1.9.0 (09:40) vs v1.6.0 (kemudian) | baris 34 vs 139 | Selesaikan |
| F-14 | Percanggahan Bil. Ujian Bun: 49/49 vs 62/62 — kedua-dua 2026-09-12 | baris 120 vs 188 | Selesaikan |
| F-15 | "PID 15260" dikunci sebagai fakta — PID berubah setiap restart | ARCH baris 40; README baris 54 | Ganti → "persistent background process" |
| F-16 | Dakwaan "Sifar emoji sebagai ikon" dilanggar dokumen sendiri (katalog penuh emoji; dock Doh-Nut guna 🍩) + bercanggah AGENTS §3.2 | README katalog vs `index.html` | Selaraskan polisi |
| F-17 | `tabular-nums` dakwaan "semua nilai RM" — hanya 3 kegunaan | grep: 3 | Kaji semula ayat atau tambah kegunaan |
| F-18 | `backend/auth.py` + `test_auth.py` wujud & diuji (9 test) tapi TIDAK disebut dalam mana-mana doc; guard `telegram_auth_guard` tiada penggunaan dalam routers (grep: 0) — sistem sebenarnya zero-auth sedangkan doc kata "Zero-Trust" | `auth.py:68` | Dokumen status auth sebenar ATAU wire-kan guard |
| F-19 | "Eksklusif 127.0.0.1:9220" — fallback port bermakna boleh jalan di 9230/9225/dll. | `main.py:18` | Laraskan ayat |
| F-20 | Contoh respons `ai-labs/focus`: `{"focused_lab": ...}` vs kod sebenar `{"target": ...}` | `dohnut.py:262` | Betulkan doc |

## ✅ Dakwaan Yang Disahkan BETUL (16 item — rujuk review penuh)

Fallback port `[9230, 9225, 9255, 9290, 8080]` (`main.py:18`) · 5 laluan WebSocket · data Doh-Nut tepat hingga sen (`dohnut.py:56-96`) · 6-platform social · 4 nod swarm · `data-idx="16"` · JetBrains Mono (10×) + tabular-nums (3×) · test_websockets_e2e.py · deploy files · manifest.json + 15 ikon · skrip repo · laluan venv (`dohnut.py:269`) · Obsidian 2,700+ nota.

---

# 🚦 Status Pelaksanaan

| Fasa | Kandungan | Risiko | Status |
|:---:|:---|:---:|:---:|
| 0 | git init + baseline + .gitignore | 0 | ⬜ Belum |
| 1 | Junk, log → var\log, pid → var\run, archive, tools\mcp, scripts subfolder, docs\README.md | 0 | ⬜ Belum |
| 2 | db → var\lib (edit `dohnut.py:35`) + pytest | Rendah | ⬜ Belum |
| 3 | Pembetulan destinasian log dalam launch config | Rendah | ⬜ Belum |
| 4 | Pemetaan scripts\ penuh + commit pengesahan | 0 | ⬜ Belum |
| P0 | F-01..F-04 (backlog Bahagian B) | — | ⬜ Belum |
| P1 | F-05..F-08 | — | ⬜ Belum |
| P2 | F-09..F-20 | — | ⬜ Belum |

---

# 📄 Rujukan

- [12-Factor App — Factor XI: Logs](https://12factor.net/logs) · [Factor III: Config](https://12factor.net/config)
- [FastAPI Official Full-Stack Template](https://github.com/tiangolo/full-stack-fastapi-template)
- [PyPA sampleproject](https://github.com/pypa/sampleproject)
- [FHS 3.0 (Filesystem Hierarchy Standard)](https://en.wikipedia.org/wiki/Filesystem_Hierarchy_Standard)
- [Divio Documentation System](https://docs.divio.com/)
- Dokumen berkaitan: `docs/PRD.md` · `docs/ARCHITECTURE.md` · `docs/AGENTS.md` · `README.md` · `docs/SECURITY.md`

---

<div align="center">
  <b>GLM IMPROVEMENT PLAN v1.0.0 — RESEARCH-VALIDATED · READY FOR EXECUTION</b>
</div>
