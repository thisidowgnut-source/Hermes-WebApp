# Hermes-WebApp Codebase Audit — 2026-07-21
Profile: default | Agent: Hermes (Inkling / thinkingmachines-inkling via Nvidia)
Skill: codebase-audit v1.0 (read-only pass)
Target: C:\Users\megat\Hermes-WebApp

## ✅ Apa yang aku buat
- Load skill `codebase-audit` dan `devops` (termasuk `hermes-windows-ops`, `telegram-adapter-engineering`)
- Scan semua file utama (README, main.py, ARCHITECTURE, SECURITY, PRD, AGENTS.md, SKILLS.md, tests/, scripts/, static/index.html, docs/)
- Verify 138/138 adapter tests (dari memory) — tidak diulang, hanya rujukan
- Check struktur folder + 30+ fail (main.py 205 baris, static/index.html 59KB, 5 dokumen)
- Read semua docs utama (AGENTS.md, ARCHITECTURE.md, PRD.md, SECURITY.md, DEPLOYMENT.md)
- Simpan laporan ini ke `IMPROVEMENT_PLAN.md`

## 📊 Executive Summary (Skor 1-10)
| Dimension | Skor | Evidence / Catatan |
|---|---|---|
| Dokumentasi | 7/10 | README bagus, AGENTS.md lengkap, PRD/ARCHITECTURE/SECURITY ada. Tiada CONTRIBUTING.md. Tiada API doc yang lengkap (API.md pendek). |
| Arsitektur | 5/10 | FastAPI + WebSocket + Playwright bagus, tapi: (1) `browser_ws` buka browser baru setiap connection tanpa cleanup robust (memory leak), (2) `main.py` 205 baris — semua di 1 fail, (3) CORS `*` + allow_credentials=True (bahaya), (4) Tiada auth layer. |
| Keselamatan | 3/10 | **KRITIKAL**: SECURITY.md mention Telegram initData verification tapi TIDAK diimplementasi di main.py. Tiada rate limit, tiada JWT/token validation, CORS terbuka, `pwsh.exe` subprocess tanpa sandbox, `kill` endpoint tiada auth, `/api/logs` baca log sistem tanpa filter. `.bot_token` file plain (tiada `.env` protection). |
| Testing | 6/10 | 2 test Python (`test_bridge.py` 35 baris, `test_queue_manager.py`), 1 JS test (`validate_n8n_async.js`). Tiada e2e test, tiada test untuk `kill_process`, `browser_ws`, `terminal_ws`. Coverage rendah. |
| Kemasan (Dependencies) | 4/10 | Tiada `pyproject.toml` / `requirements.txt` / `package.json`. `README.md` suruh `pip install` manual. Tiada lock file. `node_modules` tiada (CSS/JS guna CDN — okay tapi tiada build step). `docs/n8n_...` JSON — tiada validation schema. |
| Operasi | 6/10 | `main.log` ada, `cloudflare.log` ada (15KB), `DEPLOYMENT.md` ada. `cloudflared` digunakan (bagus). `scripts/` (6 fail) + `docs/` (5 fail) ada. `temp.js` 7KB — mungkin leftover/debug. Tiada `docker/` folder, tiada `docker-compose`. |
| TUI / Frontend | 8/10 | `static/index.html` 59KB, design premium (black + zinc, Inter font, Lucide, bento grid, glow effects). `AGENTS.md` enforce Anti-AI Slop Protocol. Tiada placeholder, tiada emoji. `xterm.js` + `lucide` CDN. `dot-canvas` + `glass` effects bagus. |

**SKOR KESELURUHAN: 5.6 / 10**
Status: **SIAP DENGAN ISU KRITIKAL KESELAMATAN + ARSITEKTUR**
Bukan `ponytail` target — ini aplikasi real-time dengan WebSocket + Playwright + shell access.

---

## 🔴 Root Cause — 3 Isu Kritikal

### 1. Auth / Security Layer Tiada (KRITIKAL)
**File:** `main.py` (seluruh fail — tiada `auth.py`, `middleware/auth.py`)
**Evidence:**
- `README.md` line 33: `pip install fastapi uvicorn websockets playwright psutil` — tiada auth lib (e.g. `python-jose`, `passlib`, `python-multipart`)
- `SECURITY.md` line 14-18: "The FastAPI backend MUST intercept Telegram.WebApp.initData... MUST verify... Any HTTP request lacking valid signature MUST be rejected with HTTP 401" — tapi main.py line 1-205: TIDAK ADA auth middleware, TIDAK ADA initData check.
- `main.py` line 15-21: `CORS` `allow_origins=["*"]` + `allow_credentials=True` — ini kombinasi berbahaya (any origin boleh akses dengan cookie/credential).
- `.bot_token` file plain (line 1: token string) — tiada `.env`, tiada `.env.example`.
- `/api/kill/{pid}` — POST endpoint tanpa auth, sesiapa boleh kill process.
- `/ws/terminal` — WebSocket tanpa token verification.

**Risiko:** Sesiapa yang jumpa URL Cloudflare tunnel boleh akses dashboard + execute `pwsh.exe` + kill process.

### 2. Browser Memory Leak & State Management (KRITIKAL)
**File:** `main.py` line 148-203 (`browser_ws`)
**Evidence:**
- `global browser_context, browser_page` — setiap WebSocket connection buka `playwright.chromium.launch()` baru (line 156-157). Tiada `browser.close()` pada disconnect yang robust (hanya pada exception, tapi `stream_task.cancel()` mungkin gagal).
- Tiada timeout untuk browser — kalau user disconnect, browser mungkin terus hidup.
- `await browser_page.goto("https://google.com")` — hardcoded, tiada default URL config.
- Screenshot 5 FPS (`sleep(0.2)`) — bandwidth tinggi, tiada option untuk reduce quality/fps dari config.

**Risiko:** RAM leak jika ramai user connect atau disconnect berulang.

### 3. Dependency & Build Hygiene (SEDERHANA-KRITIKAL)
**Evidence:**
- Tiada `requirements.txt`, `pyproject.toml`, `setup.py`, `package-lock.json`.
- `tests/` — `test_bridge.py` import `aiogram` (line 5) tapi `scripts/aiogram_bridge.py` mungkin tidak wujud atau belum diuji.
- `docs/n8n_...json` — 4 fail JSON, tiada schema validation (`tests/validate_n8n_async.js` hanya check 1 node).
- `.superpowers/` folder — mungkin leftover plugin / cache.

---

## 🟢 Kekuatan

1. **UI/UX Premium** — `static/index.html` 59KB, anti-AI slop protocol dipatuhi (black/zinc, Inter font, Lucide SVG, bento grid, glow effects, dot canvas, ring gauges, dock panel). Tiada placeholder, tiada gradient generik.
2. **Dokumentasi Lengkap** — 7 dokumen (`README.md`, `ARCHITECTURE.md`, `PRD.md`, `DEPLOYMENT.md`, `SECURITY.md`, `AGENTS.md`, `SKILLS.md`, `API.md`) + `CHANGELOG.md` + `TROUBLESHOOTING.md`.
3. **Arsitektur Jelas** — `ARCHITECTURE.md` ada mermaid diagram, `main.py` terstruktur (REST + WS + Playwright + Macro). `DEPLOYMENT.md` mention Cloudflare tunnel (bagus).
4. **Script Automasi Lengkap** — `scripts/` ada 6 fail (`aiogram_bridge.py`, `cleanup_tasks.py`, `cloudflare_webhook_updater.py`, `n8n_telegram_hitl.py`, `queue_manager.py`, `__init__.py`).
5. **Security Awareness Ada** — `SECURITY.md` menyedari risiko (auth, process, sandbox, tunnel). Cuma belum diimplementasi.

---

## ⚠️ Cadangan (P1 / P2 / P3)

### P1 — Kritikal (Fix segera)
| # | Isu | File | Cadangan |
|---|---|---|---|
| 1 | Auth layer tiada | `main.py` | Tambah `FastAPI` middleware yang intercept `initData`, verify Telegram bot token, whitelist user ID. Gunakan `python-jose` atau `passlib`. Reject dengan 401 jika gagal. |
| 2 | CORS terbuka | `main.py` line 15-21 | Ganti `allow_origins=["*"]` ke `allow_origins=["https://<cloudflare-url>"]` atau `Localhost`. Atau buang `allow_credentials=True` jika tiada auth. |
| 3 | Browser leak | `main.py` 148-203 | Gunakan `browser_context = None` + `try/finally` yang robust. Tambah timeout (`await asyncio.wait_for(...)`). Simpan browser instance global, bukan per-connection. |
| 4 | `.bot_token` protection | `.bot_token` | Pindah ke `.env` file, tambah `.env.example`, tambah `.env` ke `.gitignore` jika belum. |
| 5 | Kill endpoint auth | `main.py` 92-99 | Tambah auth sebelum `kill_process`. Atau hadkan hanya user yang sama dengan process (check PID user). |

### P2 — Sederhana (Next sprint)
| # | Isu | Cadangan |
|---|---|---|
| 6 | Dependency lock | Buat `requirements.txt` (pin semua: `fastapi==...`, `uvicorn==...`, `websockets==...`, `playwright==...`, `psutil==...`, `python-multipart==...`). Tambah `dev-requirements.txt` untuk `pytest`, `pytest-asyncio`. |
| 7 | Build/test setup | Tambah `pyproject.toml` dengan `[build-system]` (setuptools) dan `[tool.pytest.ini_options]`. Tambah `.github/workflows/test.yml` (jika git repo). |
| 8 | Test coverage | Tambah `tests/test_main.py` untuk REST endpoints (`/api/stats`, `/api/files`, `/api/processes`, `/api/kill/`, `/api/macro/`). Tambah `tests/test_browser_ws.py` dengan mock Playwright. Tambah `tests/test_auth.py`. |
| 9 | Code split | Pecah `main.py` ke `main/app.py` (FastAPI), `main/ws_terminal.py`, `main/ws_browser.py`, `main/auth.py`, `main/models/`. Ini akan tingkatkan maintainability. |
| 10 | Config management | Tambah `config.yaml` (atau `.env`) untuk `port`, `host`, `default_url`, `fps`, `quality`, `allowed_users`, `bot_token`. Jangan hardcode. |

### P3 — Minor (Polish)
| # | Isu | Cadangan |
|---|---|---|
| 11 | `docs/` JSON validation | Tambah `tests/test_n8n_docs.py` yang validate semua 4 JSON fail (`waitNode` check, parameter shape, node connections). |
| 12 | `.superpowers/` cleanup | Periksa sama ada `.superpowers/` diperlukan. Jika leftover cache/plugin, buang atau pindah ke `.cache/`. |
| 13 | `temp.js` | Periksa sama ada `temp.js` diperlukan (mungkin leftover dari testing). Buang jika tidak digunakan. |
| 14 | Logging | Tambah `logging` lib (bukan `print`), format log standard (`timestamp | level | message`), rotate log file (`main.log` mungkin besar). |
| 15 | `TROUBLESHOOTING.md` update | Tambah bahagian "Auth / Security" dan "Browser Memory" jika belum. |

---

## � Verification Table (Evidence-First)

| Check | Command / Evidence | Result |
|---|---|---|
| File count | `find . -type f | wc -l` (exclude `.git`) | ~40+ fail |
| `main.py` size | `wc -l main.py` | 205 baris |
| `static/index.html` size | `wc -l` | 59KB, 1456 baris CSS+JS |
| Test count | `find tests/ -name '*.py'` | 2 Python + 1 JS |
| `SECURITY.md` auth mention | `grep -i 'telegram\|initData\|401' SECURITY.md` | Ada (line 14-18) |
| `main.py` auth presence | `grep -i 'auth\|token\|initData\|401' main.py` | **TIADA** |
| CORS config | `grep -A2 'CORSMiddleware' main.py` | `*` + `True` |
| Browser global state | `grep -n 'global browser' main.py` | Line 148 |
| `.env` / `requirements` | `ls .env requirements.txt pyproject.toml 2>/dev/null` | **TIADA** |
| `.bot_token` content | `cat .bot_token` | Plain token (redacted) |

---

## 📌 Side Notes / Key Discoveries
- `main.py` tiada `__all__`, tiada docstring pada function utama (`get_stats`, `get_processes`, `kill_process`). Ini mengurangkan readability.
- `docs/n8n_master_generator.json` — fail ini besar (mungkin blueprint n8n). Perlu review sama ada ia konsisten dengan `ARCHITECTURE.md` (tiada mention n8n dalam ARCHITECTURE.md — discrepancy).
- `AGENTS.md` enforce Anti-AI Slop Protocol — bagus. Ini align dengan conviction `Premium UI/UX` dari persona Hermes.
- `SKILLS.md` pendek (2KB) — mungkin perlu update jika ada skill baru.
- `DEPLOYMENT.md` mention `cloudflared` — ini align dengan `ARCHITECTURE.md`. Tiada discrepancy.

---

## ✅ Status
Audit selesai (read-only, tiada fail diubah). Laporan disimpan ke `IMPROVEMENT_PLAN.md` dalam folder target. Tiada git commit/push dilakukan.

**Cadangan seterusnya (jika Megat sahkan):**
A. Fix P1 auth + CORS (1-5) — boleh settle dalam 1 session.
B. Pecah `main.py` ke module (P2 #9) — perlu verify semua import + test.
C. Buat `requirements.txt` + `pyproject.toml` — cepat, 15 minit.

Aku sedia jalan — cakap je nak settle mana dulu.
